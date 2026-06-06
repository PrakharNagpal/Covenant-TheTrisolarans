// Lane: P3 frontend
import type { Alert, Decision, LineageLink } from "@/lib/api";

export const mockDecisions: Decision[] = [
  {
    id: "dec-001",
    summary: "JWT for all auth — stateless, works for mobile",
    rationale: "Sessions need sticky servers. JWT scales horizontally.",
    participants: ["@alice", "@bob"],
    date: "Jan 14",
    source: "slack",
  },
  {
    id: "dec-002",
    summary: "3-step checkout — single-page had 23% higher abandonment",
    rationale: "User testing on 60 participants. 3-step won clearly.",
    participants: ["@design-lead"],
    date: "Feb 28",
    source: "notion",
  },
  {
    id: "dec-003",
    summary: "Postgres over MongoDB — relational integrity non-negotiable",
    rationale: "Decision graphs need foreign keys + ACID.",
    participants: ["@priya", "@raj"],
    date: "Feb 3",
    source: "github",
  },
];

export const mockAlerts: Alert[] = [
  {
    id: "alert-001",
    decision_id: "dec-001",
    severity: "structural",
    source: "GitHub",
    source_ref: "trisolarans/covenant-demo@001",
    message: "New auth code introduces sessions despite the JWT decision.",
    status: "open",
    created_at: "2026-06-06T10:00:00.000Z",
    decision: mockDecisions[0],
  },
];

export const mockLineage: LineageLink[] = [
  {
    id: "lineage-001",
    decision_id: "dec-001",
    type: "Code",
    label: "Auth middleware",
    target: "src/auth/middleware.ts:1-87",
    source: "GitHub",
    note: "Validates JWT bearer tokens before protected route access.",
  },
  {
    id: "lineage-002",
    decision_id: "dec-001",
    type: "Spec",
    label: "Mobile login notes",
    target: "notion://decision-ledger/jwt-auth",
    source: "Notion",
    note: "Documents why mobile clients should not depend on server sessions.",
  },
  {
    id: "lineage-003",
    decision_id: "dec-001",
    type: "Test",
    label: "Auth regression tests",
    target: "tests/auth/session_regression.test.ts:12-62",
    source: "GitHub",
    note: "Catches session-based auth regressions before review.",
  },
  {
    id: "lineage-004",
    decision_id: "dec-002",
    type: "Design",
    label: "Checkout flow spec",
    target: "figma://checkout-v4/flow",
    source: "Notion",
    note: "Three-step sequence used by web and mobile checkout.",
  },
  {
    id: "lineage-005",
    decision_id: "dec-003",
    type: "Schema",
    label: "Billing schema",
    target: "db/schema/billing.sql:1-144",
    source: "GitHub",
    note: "Relational billing tables inherit the Postgres decision.",
  },
];
