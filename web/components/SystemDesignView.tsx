"use client";

import { useMemo, useState } from "react";
import type { CSSProperties } from "react";
import type { LucideIcon } from "lucide-react";
import {
  AlertTriangle,
  Bell,
  BrainCircuit,
  CheckCircle2,
  ClipboardList,
  Database,
  FileText,
  GitBranch,
  GitCommit,
  GitPullRequest,
  MessageSquare,
  RefreshCw,
  Send,
  Server,
  ShieldCheck,
  Workflow,
} from "lucide-react";

type LaneKey = "overview" | "slack" | "github" | "linear";

type FlowStep = {
  id: string;
  title: string;
  detail: string;
  endpoint?: string;
  icon: LucideIcon;
};

type Lane = {
  key: LaneKey;
  label: string;
  accent: string;
  soft: string;
  icon: LucideIcon;
  signal: string;
  outcome: string;
  steps: FlowStep[];
  notes: string[];
};

const lanes: Lane[] = [
  {
    key: "overview",
    label: "Covenant",
    accent: "#7B6CF6",
    soft: "#F5F3FF",
    icon: ShieldCheck,
    signal: "Webhook events become durable team memory and contradiction alerts.",
    outcome: "Shared pipeline: verify, normalize, classify, compare, store, notify.",
    steps: [
      {
        id: "sources",
        title: "Sources",
        detail: "Slack, GitHub, Linear, and Notion create the raw signal.",
        icon: Workflow,
      },
      {
        id: "webhooks",
        title: "Webhook Router",
        detail: "FastAPI routes verify signatures and choose a background worker.",
        endpoint: "/webhooks/*",
        icon: Server,
      },
      {
        id: "memory",
        title: "Decision Memory",
        detail: "Supabase decisions, alerts, lineage, and pending overwrite records.",
        icon: Database,
      },
      {
        id: "reasoning",
        title: "Contradiction Engine",
        detail: "Classifier and contradiction checks compare new evidence to prior decisions.",
        icon: BrainCircuit,
      },
      {
        id: "notify",
        title: "Notifications",
        detail: "Covenant posts where the work happened and raises ledger alerts.",
        icon: Bell,
      },
    ],
    notes: [
      "Every inbound path is asynchronous after signature verification.",
      "Alerts keep a source reference so the ledger can trace back to Slack, GitHub, or Linear.",
      "The same contradiction engine is reused for code diffs, Slack decisions, and Linear comments.",
    ],
  },
  {
    key: "slack",
    label: "Slack",
    accent: "#E01E5A",
    soft: "#FFF0F8",
    icon: MessageSquare,
    signal: "Channel messages and interactive overwrite actions.",
    outcome: "New decisions are inserted, or conflicts become overwrite prompts in-thread.",
    steps: [
      {
        id: "slack-event",
        title: "Message Event",
        detail: "Slack sends event_callback for channel messages with channel, ts, user, and text.",
        endpoint: "/webhooks/slack",
        icon: MessageSquare,
      },
      {
        id: "slack-user",
        title: "User Resolution",
        detail: "Slack user IDs are resolved to display handles before the decision row is saved.",
        icon: ClipboardList,
      },
      {
        id: "slack-classify",
        title: "Decision Classifier",
        detail: "The message is classified as DECISION, DISCUSSION, or NOISE.",
        icon: BrainCircuit,
      },
      {
        id: "slack-compare",
        title: "Conflict Check",
        detail: "Same-role deterministic checks run first, then the contradiction engine compares memory.",
        icon: AlertTriangle,
      },
      {
        id: "slack-write",
        title: "Ledger Or Prompt",
        detail: "Clean decisions are stored. Conflicts create a pending overwrite with yes/no Slack buttons.",
        icon: Send,
      },
    ],
    notes: [
      "URL verification returns Slack challenge immediately.",
      "Form-encoded interaction payloads handle overwrite confirmation buttons.",
      "Slack source_ref is channel/ts, so duplicate webhook deliveries do not create duplicate decisions.",
    ],
  },
  {
    key: "github",
    label: "GitHub",
    accent: "#238636",
    soft: "#F0F9FF",
    icon: GitBranch,
    signal: "Push events, pull_request events, compare diffs, and PR file patches.",
    outcome: "Contradictions post as commit comments or PR conversation comments.",
    steps: [
      {
        id: "github-signature",
        title: "Signature Gate",
        detail: "GitHub HMAC verifies x-hub-signature-256 before work is queued.",
        endpoint: "/webhooks/github",
        icon: ShieldCheck,
      },
      {
        id: "github-route",
        title: "Event Split",
        detail: "push events use compare diffs; pull_request events fetch the changed PR files.",
        icon: GitPullRequest,
      },
      {
        id: "github-diff",
        title: "Patch Extraction",
        detail: "Changed files are flattened into File blocks for the contradiction engine.",
        icon: GitCommit,
      },
      {
        id: "github-compare",
        title: "Decision Compare",
        detail: "The diff is checked against existing team decisions and demo cache shortcuts.",
        icon: BrainCircuit,
      },
      {
        id: "github-comment",
        title: "GitHub Comment",
        detail: "Pushes get commit comments. PRs get issue-thread conversation comments.",
        icon: Send,
      },
    ],
    notes: [
      "PR comments use GitHub issue comments because PR conversations share the issues API.",
      "Push comments still target /commits/{sha}/comments.",
      "The GitHub token needs permission to read pull request files and write issue/PR comments.",
    ],
  },
  {
    key: "linear",
    label: "Linear",
    accent: "#5E6AD2",
    soft: "#EEF0FF",
    icon: FileText,
    signal: "Comment create webhooks from Linear issues.",
    outcome: "Comment decisions are checked and contradictions are stored as Covenant alerts.",
    steps: [
      {
        id: "linear-signature",
        title: "Signature Gate",
        detail: "Linear signature verification protects the webhook route before JSON parsing.",
        endpoint: "/webhooks/linear",
        icon: ShieldCheck,
      },
      {
        id: "linear-filter",
        title: "Comment Filter",
        detail: "Only Comment create events are sent to the Linear comment processor.",
        icon: ClipboardList,
      },
      {
        id: "linear-classify",
        title: "Classifier",
        detail: "Comment body text is classified to decide whether it contains a decision.",
        icon: BrainCircuit,
      },
      {
        id: "linear-compare",
        title: "Memory Compare",
        detail: "Decision-like comments are compared with the full decision table.",
        icon: Database,
      },
      {
        id: "linear-alert",
        title: "Alert Row",
        detail: "Contradictions are inserted into alerts with the Linear comment ID as source_ref.",
        icon: AlertTriangle,
      },
    ],
    notes: [
      "Current Linear flow records Covenant alerts; outbound Linear replies are not yet implemented.",
      "The webhook is intentionally narrow: it ignores non-comment Linear events.",
      "Linear comments use the same classifier and contradiction code as the rest of Covenant.",
    ],
  },
];

const sharedStages = [
  { label: "Verify", icon: ShieldCheck },
  { label: "Queue", icon: RefreshCw },
  { label: "Classify", icon: BrainCircuit },
  { label: "Compare", icon: AlertTriangle },
  { label: "Persist", icon: Database },
  { label: "Notify", icon: Send },
] as const;

function laneByKey(key: LaneKey) {
  return lanes.find((lane) => lane.key === key) ?? lanes[0];
}

function pillStyle(lane: Lane, active: boolean): CSSProperties {
  return {
    background: active ? lane.accent : "var(--panel)",
    borderColor: active ? lane.accent : "var(--border)",
    color: active ? "white" : "var(--text-muted)",
    boxShadow: active ? `0 10px 24px ${lane.accent}33` : "var(--shadow)",
  };
}

export function SystemDesignView() {
  const [activeLaneKey, setActiveLaneKey] = useState<LaneKey>("overview");
  const activeLane = laneByKey(activeLaneKey);
  const [activeStepId, setActiveStepId] = useState(activeLane.steps[0].id);

  const activeStep = useMemo(() => {
    return activeLane.steps.find((step) => step.id === activeStepId) ?? activeLane.steps[0];
  }, [activeLane, activeStepId]);

  function selectLane(key: LaneKey) {
    const nextLane = laneByKey(key);
    setActiveLaneKey(key);
    setActiveStepId(nextLane.steps[0].id);
  }

  return (
    <main className="min-h-screen bg-[var(--app-bg)] text-[var(--text)]">
      <section className="border-b border-[var(--border)] bg-[var(--panel)]">
        <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:py-10">
          <div className="grid gap-7 lg:grid-cols-[minmax(0,0.92fr)_minmax(440px,1fr)] lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-[var(--radius-full)] border border-[var(--border)] bg-[var(--panel-soft)] px-3 py-1.5 text-xs font-extrabold uppercase tracking-[0.16em] text-[var(--text-soft)]">
                <Workflow className="h-4 w-4 text-[var(--primary)]" />
                System Design
              </div>
              <h1 className="mt-4 max-w-2xl text-4xl font-black leading-tight text-[var(--text)] sm:text-5xl">
                Webhooks, memory, and contradiction checks in one view
              </h1>
              <p className="mt-4 max-w-2xl text-base font-medium leading-7 text-[var(--text-muted)]">
                Explore how Slack, GitHub, and Linear enter Covenant, how each event is processed, and where the system writes back to humans.
              </p>
            </div>

            <div className="grid gap-2 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--panel-soft)] p-3 shadow-[var(--shadow)] sm:grid-cols-3">
              {sharedStages.map((stage, index) => {
                const StageIcon = stage.icon;
                return (
                  <div
                    className="flex min-h-[72px] items-center gap-3 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--panel)] px-3"
                    key={stage.label}
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-sm)] bg-[var(--primary-soft)] text-[var(--primary)]">
                      <StageIcon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-[11px] font-black uppercase tracking-[0.16em] text-[var(--text-soft)]">
                        {String(index + 1).padStart(2, "0")}
                      </p>
                      <p className="text-sm font-extrabold text-[var(--text)]">{stage.label}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-6 sm:px-8">
        <div className="flex flex-wrap gap-2">
          {lanes.map((lane) => {
            const LaneIcon = lane.icon;
            const active = lane.key === activeLaneKey;
            return (
              <button
                aria-pressed={active}
                className="inline-flex h-10 items-center gap-2 rounded-[var(--radius-sm)] border px-3 text-sm font-extrabold"
                key={lane.key}
                onClick={() => selectLane(lane.key)}
                style={pillStyle(lane, active)}
                type="button"
              >
                <LaneIcon className="h-4 w-4" />
                {lane.label}
              </button>
            );
          })}
        </div>

        <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
          <section className="rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
            <header className="flex flex-col gap-4 border-b border-[var(--border)] pb-4 md:flex-row md:items-center md:justify-between">
              <div className="flex items-start gap-3">
                <div
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[var(--radius-sm)] text-white"
                  style={{ background: activeLane.accent }}
                >
                  <activeLane.icon className="h-6 w-6" />
                </div>
                <div>
                  <h2 className="text-xl font-black text-[var(--text)]">
                    {activeLane.label} webhook lane
                  </h2>
                  <p className="mt-1 max-w-2xl text-sm font-medium leading-6 text-[var(--text-muted)]">
                    {activeLane.signal}
                  </p>
                </div>
              </div>
              <div
                className="rounded-[var(--radius-sm)] border px-3 py-2 text-sm font-bold leading-5"
                style={{
                  background: activeLane.soft,
                  borderColor: `${activeLane.accent}33`,
                  color: activeLane.accent,
                }}
              >
                {activeLane.outcome}
              </div>
            </header>

            <div className="relative mt-5 overflow-hidden rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--panel-soft)] p-4">
              <svg
                aria-hidden="true"
                className="pointer-events-none absolute inset-0 h-full w-full opacity-70"
                preserveAspectRatio="none"
              >
                <path
                  d="M 60 92 C 190 18, 310 160, 440 92 S 690 18, 820 92 S 1050 160, 1180 92"
                  fill="none"
                  stroke={activeLane.accent}
                  strokeDasharray="8 9"
                  strokeLinecap="round"
                  strokeWidth="2"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>

              <div
                className="relative grid gap-3"
                style={{ gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}
              >
                {activeLane.steps.map((step, index) => {
                  const StepIcon = step.icon;
                  const active = step.id === activeStep.id;
                  return (
                    <button
                      className="min-h-[142px] rounded-[var(--radius-sm)] border p-3 text-left shadow-[var(--shadow)]"
                      key={step.id}
                      onClick={() => setActiveStepId(step.id)}
                      style={{
                        background: active ? activeLane.soft : "var(--panel)",
                        borderColor: active ? activeLane.accent : "var(--border)",
                        transform: active ? "translateY(-2px)" : "none",
                      }}
                      type="button"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div
                          className="flex h-9 w-9 items-center justify-center rounded-[var(--radius-sm)] text-white"
                          style={{ background: activeLane.accent }}
                        >
                          <StepIcon className="h-4 w-4" />
                        </div>
                        <span className="text-xs font-black text-[var(--text-soft)]">
                          {String(index + 1).padStart(2, "0")}
                        </span>
                      </div>
                      <h3 className="mt-4 text-sm font-black leading-5 text-[var(--text)]">
                        {step.title}
                      </h3>
                      {step.endpoint ? (
                        <p className="mt-2 inline-flex rounded-[var(--radius-sm)] bg-[var(--panel-soft)] px-2 py-1 font-mono text-[11px] font-bold text-[var(--text-muted)]">
                          {step.endpoint}
                        </p>
                      ) : null}
                    </button>
                  );
                })}
              </div>
            </div>
          </section>

          <aside className="rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
            <div
              className="inline-flex h-10 w-10 items-center justify-center rounded-[var(--radius-sm)] text-white"
              style={{ background: activeLane.accent }}
            >
              <activeStep.icon className="h-5 w-5" />
            </div>
            <p className="mt-4 text-xs font-black uppercase tracking-[0.18em] text-[var(--text-soft)]">
              Selected Step
            </p>
            <h3 className="mt-2 text-2xl font-black leading-tight text-[var(--text)]">
              {activeStep.title}
            </h3>
            <p className="mt-3 text-sm font-medium leading-6 text-[var(--text-muted)]">
              {activeStep.detail}
            </p>
            {activeStep.endpoint ? (
              <div className="mt-4 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--panel-soft)] p-3">
                <p className="text-[11px] font-black uppercase tracking-[0.16em] text-[var(--text-soft)]">
                  Endpoint
                </p>
                <p className="mt-1 break-all font-mono text-sm font-bold text-[var(--text)]">
                  {activeStep.endpoint}
                </p>
              </div>
            ) : null}
            <div className="mt-5 border-t border-[var(--border)] pt-4">
              <p className="mb-3 text-xs font-black uppercase tracking-[0.18em] text-[var(--text-soft)]">
                Design Notes
              </p>
              <div className="grid gap-2">
                {activeLane.notes.map((note) => (
                  <div className="flex gap-2 text-sm font-medium leading-6 text-[var(--text-muted)]" key={note}>
                    <CheckCircle2 className="mt-1 h-4 w-4 shrink-0" style={{ color: activeLane.accent }} />
                    <span>{note}</span>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
