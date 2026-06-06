// Lane: P3 frontend
import type { Alert, Decision, LineageLink } from "@/lib/api";

export const mockDecisions: Decision[] = [
  {
    id: "jwt-001",
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
    decision_id: "jwt-001",
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
    id: "lineage-jwt-001",
    decision_id: "jwt-001",
    type: "file",
    label: "src/auth/jwtGuard.ts",
    target: "src/auth/jwtGuard.ts",
    source: "github",
    note: "Token verification logic",
  },
  {
    id: "lineage-jwt-002",
    decision_id: "jwt-001",
    type: "route",
    label: "api/v1/auth/refresh",
    target: "api/v1/auth/refresh",
    source: "github",
    note: "Refresh token endpoint",
  },
  {
    id: "lineage-jwt-003",
    decision_id: "jwt-001",
    type: "file",
    label: "src/middleware/auth.ts",
    target: "src/middleware/auth.ts",
    source: "github",
    note: "Wraps all protected routes",
  },
];
