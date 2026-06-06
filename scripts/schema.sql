-- Lane: P2 backend
-- Run this in the Supabase SQL editor (enable pgvector extension first)
-- Dashboard → Database → Extensions → enable "vector"

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS decisions (
  id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  summary     text NOT NULL,
  rationale   text,
  participants text[],
  alternatives_rejected jsonb DEFAULT '[]'::jsonb,
  source      text,
  source_ref  text,
  embedding   vector(1536),
  created_at  timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS lineage_links (
  id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  decision_id uuid REFERENCES decisions(id) ON DELETE CASCADE,
  artifact_type text,    -- e.g. "file", "pr", "issue"
  artifact_ref text,
  note        text,
  created_at  timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS alerts (
  id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  decision_id uuid REFERENCES decisions(id) ON DELETE SET NULL,
  severity    text,
  source      text,
  source_ref  text,
  message     text,
  status      text DEFAULT 'open',
  contradiction_explanation text,
  created_at  timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pending_decision_overwrites (
  id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  source      text,
  source_ref  text,
  channel     text,
  thread_ts   text,
  new_decision jsonb NOT NULL,
  contradiction_decision_ids text[] DEFAULT '{}',
  created_at  timestamptz DEFAULT now()
);

-- Compatibility columns for projects that already ran an older copy of this file.
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS source_ref text;
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS embedding vector(1536);
ALTER TABLE decisions ALTER COLUMN alternatives_rejected DROP DEFAULT;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'decisions'
      AND column_name = 'alternatives_rejected'
      AND data_type <> 'jsonb'
  ) THEN
    ALTER TABLE decisions
      ALTER COLUMN alternatives_rejected TYPE jsonb
      USING COALESCE(to_jsonb(alternatives_rejected), '[]'::jsonb);
  END IF;
END $$;

ALTER TABLE decisions ALTER COLUMN alternatives_rejected SET DEFAULT '[]'::jsonb;

ALTER TABLE lineage_links ADD COLUMN IF NOT EXISTS artifact_ref text;
ALTER TABLE lineage_links ADD COLUMN IF NOT EXISTS note text;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'lineage_links'
      AND column_name = 'file_path'
  ) THEN
    UPDATE lineage_links
    SET artifact_ref = file_path
    WHERE artifact_ref IS NULL AND file_path IS NOT NULL;
  END IF;
END $$;

ALTER TABLE alerts ADD COLUMN IF NOT EXISTS source text;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS source_ref text;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS message text;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS status text DEFAULT 'open';
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS contradiction_explanation text;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'alerts'
      AND column_name = 'explanation'
  ) THEN
    UPDATE alerts
    SET
      message = COALESCE(message, explanation),
      contradiction_explanation = COALESCE(contradiction_explanation, explanation);
  END IF;

  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'alerts'
      AND column_name = 'source_type'
  ) THEN
    UPDATE alerts
    SET source = COALESCE(source, source_type);
  END IF;
END $$;

UPDATE alerts
SET status = COALESCE(status, 'open');

ALTER TABLE pending_decision_overwrites ADD COLUMN IF NOT EXISTS source text;
ALTER TABLE pending_decision_overwrites ADD COLUMN IF NOT EXISTS source_ref text;
ALTER TABLE pending_decision_overwrites ADD COLUMN IF NOT EXISTS channel text;
ALTER TABLE pending_decision_overwrites ADD COLUMN IF NOT EXISTS thread_ts text;
ALTER TABLE pending_decision_overwrites ADD COLUMN IF NOT EXISTS new_decision jsonb;
ALTER TABLE pending_decision_overwrites ADD COLUMN IF NOT EXISTS contradiction_decision_ids text[] DEFAULT '{}';

-- pgvector similarity search function
CREATE OR REPLACE FUNCTION match_decisions(
  query_embedding vector(1536),
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  summary text,
  rationale text,
  participants text[],
  source text,
  created_at timestamptz,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id, d.summary, d.rationale, d.participants, d.source, d.created_at,
    1 - (d.embedding <=> query_embedding) AS similarity
  FROM decisions d
  WHERE d.embedding IS NOT NULL
  ORDER BY d.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
