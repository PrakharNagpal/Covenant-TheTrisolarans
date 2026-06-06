// Lane: P3 frontend
import Link from "next/link";
import { CalendarDays, GitBranch, Users } from "lucide-react";
import type { Decision } from "@/lib/api";

type DecisionCardProps = {
  decision: Decision;
  isFlagged?: boolean;
};

const sourceStyles: Record<string, string> = {
  GitHub: "bg-[#ECE8FF] text-[#534AB7] border-[#D8D0FF]",
  Notion: "bg-[#E8F3EE] text-[#0F6E56] border-[#C6E0D5]",
  Slack: "bg-[#FFF0DD] text-[#8A4B08] border-[#F1D2A5]",
  Mock: "bg-[#E8E4D8] text-[#534AB7] border-[#D8D2C4]",
};

export function DecisionCard({ decision, isFlagged = false }: DecisionCardProps) {
  const sourceClass = sourceStyles[decision.source] ?? sourceStyles.Mock;

  return (
    <Link
      className={`group block h-full rounded-lg border bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${
        isFlagged
          ? "border-[#D85A30] ring-2 ring-[#D85A30]/20"
          : "border-[#D8D2C4]"
      }`}
      href={`/lineage?id=${encodeURIComponent(decision.id)}`}
    >
      <article className="flex h-full flex-col gap-5">
        <div className="flex items-start justify-between gap-4">
          <h2 className="text-base font-semibold leading-snug text-[#1B1A22]">
            {decision.summary}
          </h2>
          <span
            className={`shrink-0 rounded-full border px-2.5 py-1 text-xs font-semibold ${sourceClass}`}
          >
            {decision.source}
          </span>
        </div>

        <p className="line-clamp-2 min-h-10 text-sm leading-5 text-[#5D5968]">
          {decision.rationale ?? "Decision rationale is ready for lineage view."}
        </p>

        <div className="mt-auto flex flex-col gap-3 border-t border-[#EEE9DD] pt-4">
          <div className="flex items-center gap-2 text-sm text-[#5D5968]">
            <CalendarDays className="h-4 w-4 text-[#534AB7]" />
            <span>{decision.date}</span>
          </div>
          <div className="flex items-start gap-2 text-sm text-[#5D5968]">
            <Users className="mt-0.5 h-4 w-4 text-[#0F6E56]" />
            <div className="flex flex-wrap gap-2">
              {decision.participants.map((participant) => (
                <span
                  className="rounded-full bg-[#F1EFE8] px-2.5 py-1 text-xs font-semibold text-[#0F6E56]"
                  key={participant}
                >
                  {participant}
                </span>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-[#534AB7] opacity-0 transition group-hover:opacity-100">
            <GitBranch className="h-3.5 w-3.5" />
            Open lineage
          </div>
        </div>
      </article>
    </Link>
  );
}
