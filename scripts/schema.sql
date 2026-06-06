-- Run this in the Supabase SQL editor (enable pgvector extension first)
-- Dashboard → Database → Extensions → enable "vector"

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS decisions (
  id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  summary     text NOT NULL,
  rationale   text,
  participants text[],
  alternatives_rejected text,
  source      text,
  embedding   vector(1536),
  created_at  timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS lineage_links (
  id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  decision_id uuid REFERENCES decisions(id) ON DELETE CASCADE,
  artifact_type text,    -- e.g. "file", "pr", "issue"
  file_path   text,
  note        text,
  created_at  timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS alerts (
  id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  decision_id uuid REFERENCES decisions(id) ON DELETE SET NULL,
  severity    text,
  explanation text,
  confidence  float,
  source_ref  text,
  source_type text,
  created_at  timestamptz DEFAULT now()
);

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
