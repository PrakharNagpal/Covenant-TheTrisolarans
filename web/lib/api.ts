// Lane: P3 frontend
import { mockAlerts, mockDecisions, mockLineage } from "@/lib/mock";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "1";

type ApiRecord = Record<string, unknown>;

export type Decision = {
  id: string;
  summary: string;
  date: string;
  participants: string[];
  source: string;
  rationale?: string;
  alternatives_rejected?: string[];
};

export type Alert = {
  id: string;
  decision_id: string;
  severity: "cosmetic" | "behavioural" | "structural" | string;
  source: string;
  source_ref: string;
  message: string;
  status: string;
  created_at?: string;
  decision?: Decision;
};

export type LineageLink = {
  id: string;
  decision_id: string;
  type: string;
  label: string;
  target: string;
  source: string;
  note?: string;
};

export type ArchaeologyResponse = {
  answer: string;
};

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

function asRecord(value: unknown): ApiRecord {
  return value && typeof value === "object" ? (value as ApiRecord) : {};
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.length > 0 ? value : fallback;
}

function asStringArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map((item) => String(item)).filter(Boolean);
  }

  if (typeof value === "string" && value.length > 0) {
    return value
      .split(/[,;\n]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
}

function normalizeSource(value: unknown): string {
  const source = asString(value, "Unknown").toLowerCase();

  if (source.includes("github")) {
    return "github";
  }

  if (source.includes("slack")) {
    return "slack";
  }

  if (source.includes("notion")) {
    return "notion";
  }

  if (source.includes("linear")) {
    return "linear";
  }

  return source;
}

function formatDate(value: unknown): string {
  if (typeof value !== "string" || value.length === 0) {
    return "Date not recorded";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(parsed);
}

function normalizeDecision(rawValue: unknown): Decision {
  const raw = asRecord(rawValue);
  const id = asString(raw.id, "unknown-decision");
  const participants = asStringArray(raw.participants);

  return {
    id,
    summary: asString(raw.summary, "Untitled decision"),
    date: asString(raw.date) || formatDate(raw.created_at),
    participants: participants.length > 0 ? participants : ["Unknown"],
    source: normalizeSource(raw.source),
    rationale: asString(raw.rationale) || undefined,
    alternatives_rejected: asStringArray(raw.alternatives_rejected),
  };
}

function normalizeLineage(rawValue: unknown): LineageLink {
  const raw = asRecord(rawValue);
  const target =
    asString(raw.target) ||
    asString(raw.artifact_ref) ||
    asString(raw.file_path, "No ref");
  const type = asString(raw.type) || asString(raw.artifact_type, "Artifact");
  const label = asString(raw.label) || target;

  return {
    id: asString(raw.id, `${asString(raw.decision_id, "lineage")}-${target}`),
    decision_id: asString(raw.decision_id),
    type,
    label,
    target,
    source: normalizeSource(raw.source),
    note: asString(raw.note) || undefined,
  };
}

function normalizeAlert(rawValue: unknown): Alert {
  const raw = asRecord(rawValue);
  const decisionRaw = raw.decision ? normalizeDecision(raw.decision) : undefined;
  const message =
    asString(raw.message) ||
    asString(raw.contradiction_explanation) ||
    asString(raw.explanation) ||
    "A contradiction was detected.";

  return {
    id: asString(raw.id, `alert-${asString(raw.created_at, Date.now().toString())}`),
    decision_id: asString(raw.decision_id),
    severity: asString(raw.severity, "structural"),
    source: normalizeSource(raw.source || raw.source_type),
    source_ref: asString(raw.source_ref),
    message,
    status: asString(raw.status, "open"),
    created_at: asString(raw.created_at) || undefined,
    decision: decisionRaw,
  };
}

export async function getDecisions(): Promise<Decision[]> {
  if (USE_MOCK) {
    return mockDecisions;
  }

  const data = await fetchJson<unknown[]>("/api/decisions");
  return data.map(normalizeDecision);
}

export async function getDecision(id: string): Promise<Decision> {
  if (USE_MOCK) {
    const decision = mockDecisions.find((item) => item.id === id);
    if (!decision) {
      throw new Error(`Mock decision not found: ${id}`);
    }
    return decision;
  }

  const data = await fetchJson<unknown>(`/api/decisions/${id}`);
  return normalizeDecision(data);
}

export async function getLineage(id: string): Promise<LineageLink[]> {
  if (USE_MOCK) {
    return mockLineage.filter((item) => item.decision_id === id);
  }

  const data = await fetchJson<unknown[]>(`/api/decisions/${id}/lineage`);
  return data.map(normalizeLineage);
}

export async function getAlerts(since?: string | null): Promise<Alert[]> {
  if (USE_MOCK) {
    return mockAlerts;
  }

  const params = since ? `?since=${encodeURIComponent(since)}` : "";
  const data = await fetchJson<unknown[]>(`/api/alerts${params}`);
  return data.map(normalizeAlert);
}

export async function postArchaeology(
  question: string,
): Promise<ArchaeologyResponse> {
  if (USE_MOCK) {
    const normalized = question.toLowerCase();

    if (normalized.includes("jwt")) {
      return {
        answer:
          "@alice and @bob decided on Jan 14, 2026 to use JWT for auth instead of server sessions. The rationale was that stateless auth works better for mobile clients, and server sessions were rejected because they add stateful infrastructure to the request path.",
      };
    }

    if (normalized.includes("3") || normalized.includes("checkout")) {
      return {
        answer:
          "@design-lead decided on Feb 28, 2026 to keep checkout to three steps. The team wanted a short, predictable flow that reduces abandonment, while rejecting single-page and five-step checkout variants.",
      };
    }

    if (normalized.includes("postgres")) {
      return {
        answer:
          "@priya and @raj decided on Feb 3, 2026 to use Postgres as the system of record. Relational integrity mattered for billing and audits, and MongoDB was rejected for this path.",
      };
    }

    return {
      answer:
        "I do not have a matching canned decision for that yet. Try asking about JWT, checkout, or Postgres for the demo path.",
    };
  }

  const response = await fetchJson<ArchaeologyResponse | string>(
    "/api/archaeology",
    {
      body: JSON.stringify({ question }),
      method: "POST",
    },
  );

  if (typeof response === "string") {
    return { answer: response };
  }

  return response;
}
