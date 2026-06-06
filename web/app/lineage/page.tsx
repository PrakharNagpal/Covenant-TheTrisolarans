// Lane: P3 frontend
import Link from "next/link";
import type { ReactNode } from "react";
import {
  ArrowLeft,
  CalendarDays,
  ExternalLink,
  GitBranch,
  Shield,
  Users,
} from "lucide-react";
import { ParticipantPill, SourceBadge } from "@/components/DecisionCard";
import { ProductTopbar } from "@/components/ProductTopbar";
import { getDecision, getDecisions, getLineage } from "@/lib/api";

type LineagePageProps = {
  searchParams?: {
    id?: string;
  };
};

export default async function LineagePage({ searchParams }: LineagePageProps) {
  const requestedId = searchParams?.id;
  let decisions;

  try {
    decisions = await getDecisions();
  } catch (error) {
    return (
      <LineageUnavailable
        message={
          error instanceof Error
            ? error.message
            : "Could not connect to the Covenant API."
        }
      />
    );
  }

  const fallbackId = decisions[0]?.id;
  const decisionId = requestedId ?? fallbackId;

  if (!decisionId) {
    return <EmptyLineage />;
  }

  let decision;
  let lineage;

  try {
    [decision, lineage] = await Promise.all([
      getDecision(decisionId),
      getLineage(decisionId),
    ]);
  } catch (error) {
    return (
      <LineageUnavailable
        message={
          error instanceof Error
            ? error.message
            : "Could not load this decision lineage."
        }
      />
    );
  }

  return (
    <main className="app-page">
      <ProductTopbar />
      <section className="app-container flex max-w-6xl flex-col gap-8">
        <header className="app-header flex flex-col gap-6">
          <div className="flex items-center justify-between gap-4">
            <Link className="btn-secondary" href="/">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
          </div>
          <div>
            <div className="flex gap-4">
              <span className="brand-mark shrink-0">
                <Shield className="h-6 w-6" />
              </span>
              <div>
                <p className="eyebrow">Decision Lineage</p>
                <h1 className="page-title mt-1 max-w-4xl text-3xl leading-tight sm:text-4xl">
                  {decision.summary}
                </h1>
                <p className="muted mt-3 text-base font-bold">
                  Git blame, but for choices.
                </p>
              </div>
            </div>
          </div>
        </header>

        <section className="grid gap-4 lg:grid-cols-[1fr_320px]">
          <article className="panel rounded-lg p-6">
            <h2 className="text-lg font-semibold text-[var(--text)]">Why</h2>
            <p className="muted mt-3 text-base leading-7">
              {decision.rationale ?? "No rationale has been attached yet."}
            </p>

            <h3 className="mt-7 text-sm font-semibold uppercase tracking-wide text-[var(--text)]">
              Alternatives rejected
            </h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {(decision.alternatives_rejected ?? ["None recorded"]).map(
                (alternative) => (
                  <span
                    className="rounded-full bg-[var(--warning-soft)] px-3 py-1.5 text-sm font-semibold text-[var(--warning)]"
                    key={alternative}
                  >
                    {alternative}
                  </span>
                ),
              )}
            </div>
          </article>

          <aside className="panel rounded-lg p-6">
            <h2 className="text-lg font-semibold text-[var(--text)]">Provenance</h2>
            <div className="mt-5 flex flex-col gap-4">
              <MetaRow
                icon={<CalendarDays className="h-4 w-4" />}
                label="Date"
                value={decision.date}
              />
              <MetaRow
                icon={<Users className="h-4 w-4" />}
                label="Participants"
                value=""
                custom={
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {decision.participants.map((participant) => (
                      <ParticipantPill key={participant} name={participant} />
                    ))}
                  </div>
                }
              />
              <MetaRow
                icon={<GitBranch className="h-4 w-4" />}
                label="Source"
                value=""
                custom={<div className="mt-2"><SourceBadge source={decision.source} /></div>}
              />
            </div>
          </aside>
        </section>

        <section className="panel overflow-hidden rounded-lg">
          <div className="border-b border-[var(--border)] px-6 py-4">
            <h2 className="text-lg font-semibold text-[var(--text)]">
              Linked Artifacts
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] border-collapse text-left">
              <thead className="bg-[var(--panel-soft)] text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                <tr>
                  <th className="px-6 py-3">Type</th>
                  <th className="px-6 py-3">Artifact</th>
                  <th className="px-6 py-3">File path / ref</th>
                  <th className="px-6 py-3">Note</th>
                </tr>
              </thead>
              <tbody>
                {lineage.length > 0 ? (
                  lineage.map((item) => (
                    <tr className="border-t border-[var(--border)]" key={item.id}>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-[var(--accent-soft)] px-2.5 py-1 text-xs font-semibold text-[var(--accent)]">
                          {item.type}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-semibold text-[var(--text)]">
                        {item.label}
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center gap-2 font-mono text-sm text-[var(--primary)]">
                          {item.target}
                          <ExternalLink className="h-3.5 w-3.5" />
                        </span>
                      </td>
                      <td className="muted px-6 py-4 text-sm leading-6">
                        {item.note ?? "No note recorded."}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td className="muted px-6 py-8" colSpan={4}>
                      No lineage artifacts have been linked to this decision yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </section>
    </main>
  );
}

function MetaRow({
  custom,
  icon,
  label,
  value,
}: {
  custom?: ReactNode;
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex gap-3">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--accent-soft)] text-[var(--accent)]">
        {icon}
      </span>
      <span>
        <span className="soft-muted block text-xs font-semibold uppercase tracking-wide">
          {label}
        </span>
        {custom ?? (
          <span className="mt-1 block text-sm font-semibold text-[var(--text)]">
            {value}
          </span>
        )}
      </span>
    </div>
  );
}

function EmptyLineage() {
  return (
    <main className="app-page px-6 py-10">
      <div className="panel mx-auto max-w-3xl rounded-lg p-8">
        <h1 className="page-title text-2xl">
          No decision selected
        </h1>
        <Link
          className="btn-primary mt-5"
          href="/"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to ledger
        </Link>
      </div>
    </main>
  );
}

function LineageUnavailable({ message }: { message: string }) {
  return (
    <main className="app-page px-6 py-10">
      <div className="mx-auto max-w-3xl rounded-lg border border-[var(--danger)] bg-[var(--danger-soft)] p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-[var(--danger-strong)]">
          Live API unavailable
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-[var(--text)]">
          Decision lineage is waiting on FastAPI
        </h1>
        <p className="mt-3 text-sm leading-6 text-[var(--danger-strong)]">{message}</p>
        <Link
          className="btn-primary mt-6"
          href="/"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to ledger
        </Link>
      </div>
    </main>
  );
}
