// Lane: P3 frontend
import Link from "next/link";
import type { ReactNode } from "react";
import {
  ArrowLeft,
  CalendarDays,
  ExternalLink,
  GitBranch,
  Users,
} from "lucide-react";
import { getDecision, getDecisions, getLineage } from "@/lib/api";

type LineagePageProps = {
  searchParams?: {
    id?: string;
  };
};

export default async function LineagePage({ searchParams }: LineagePageProps) {
  const requestedId = searchParams?.id;
  const decisions = await getDecisions();
  const fallbackId = decisions[0]?.id;
  const decisionId = requestedId ?? fallbackId;

  if (!decisionId) {
    return <EmptyLineage />;
  }

  const [decision, lineage] = await Promise.all([
    getDecision(decisionId),
    getLineage(decisionId),
  ]);

  return (
    <main className="min-h-screen bg-[#F1EFE8] text-[#1B1A22]">
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-8 sm:px-10">
        <header className="flex flex-col gap-6 border-b border-[#D8D2C4] pb-7">
          <Link
            className="inline-flex w-fit items-center gap-2 text-sm font-semibold text-[#534AB7] hover:text-[#453DA0]"
            href="/"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to ledger
          </Link>
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-[#0F6E56]">
              Decision Lineage
            </p>
            <h1 className="mt-2 max-w-4xl text-3xl font-semibold leading-tight text-[#534AB7] sm:text-4xl">
              {decision.summary}
            </h1>
            <p className="mt-3 text-base font-medium text-[#5D5968]">
              Git blame, but for choices.
            </p>
          </div>
        </header>

        <section className="grid gap-4 lg:grid-cols-[1fr_320px]">
          <article className="rounded-lg border border-[#D8D2C4] bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-[#1B1A22]">Why</h2>
            <p className="mt-3 text-base leading-7 text-[#5D5968]">
              {decision.rationale ?? "No rationale has been attached yet."}
            </p>

            <h3 className="mt-7 text-sm font-semibold uppercase tracking-wide text-[#1B1A22]">
              Alternatives rejected
            </h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {(decision.alternatives_rejected ?? ["None recorded"]).map(
                (alternative) => (
                  <span
                    className="rounded-full bg-[#FFF0DD] px-3 py-1.5 text-sm font-semibold text-[#8A4B08]"
                    key={alternative}
                  >
                    {alternative}
                  </span>
                ),
              )}
            </div>
          </article>

          <aside className="rounded-lg border border-[#D8D2C4] bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-[#1B1A22]">Provenance</h2>
            <div className="mt-5 flex flex-col gap-4">
              <MetaRow
                icon={<CalendarDays className="h-4 w-4" />}
                label="Date"
                value={decision.date}
              />
              <MetaRow
                icon={<Users className="h-4 w-4" />}
                label="Participants"
                value={decision.participants.join(", ")}
              />
              <MetaRow
                icon={<GitBranch className="h-4 w-4" />}
                label="Source"
                value={decision.source}
              />
            </div>
          </aside>
        </section>

        <section className="overflow-hidden rounded-lg border border-[#D8D2C4] bg-white shadow-sm">
          <div className="border-b border-[#EEE9DD] px-6 py-4">
            <h2 className="text-lg font-semibold text-[#1B1A22]">
              Linked Artifacts
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] border-collapse text-left">
              <thead className="bg-[#F8F6EF] text-xs font-semibold uppercase tracking-wide text-[#5D5968]">
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
                    <tr className="border-t border-[#EEE9DD]" key={item.id}>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-[#E8F3EE] px-2.5 py-1 text-xs font-semibold text-[#0F6E56]">
                          {item.type}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-semibold text-[#1B1A22]">
                        {item.label}
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center gap-2 font-mono text-sm text-[#534AB7]">
                          {item.target}
                          <ExternalLink className="h-3.5 w-3.5" />
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm leading-6 text-[#5D5968]">
                        {item.note ?? "No note recorded."}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td className="px-6 py-8 text-[#5D5968]" colSpan={4}>
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
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex gap-3">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#E8F3EE] text-[#0F6E56]">
        {icon}
      </span>
      <span>
        <span className="block text-xs font-semibold uppercase tracking-wide text-[#8A8793]">
          {label}
        </span>
        <span className="mt-1 block text-sm font-semibold text-[#1B1A22]">
          {value}
        </span>
      </span>
    </div>
  );
}

function EmptyLineage() {
  return (
    <main className="min-h-screen bg-[#F1EFE8] px-6 py-10 text-[#1B1A22]">
      <div className="mx-auto max-w-3xl rounded-lg border border-[#D8D2C4] bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-[#534AB7]">
          No decision selected
        </h1>
        <Link
          className="mt-5 inline-flex items-center gap-2 rounded-lg bg-[#534AB7] px-4 py-2.5 text-sm font-semibold text-white"
          href="/"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to ledger
        </Link>
      </div>
    </main>
  );
}
