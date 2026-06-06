"use client";

import { useState } from "react";
import Link from "next/link";
import type { Decision } from "@/lib/api";
import { Pill } from "@/components/ui/Pill";
import { tokens } from "@/lib/tokens";

type DecisionCardProps = {
  decision: Pick<
    Decision,
    "id" | "summary" | "rationale" | "participants" | "date" | "source"
  >;
  index: number;
};

const sourceAccents: Record<
  string,
  { color: string; emoji: string; label: string }
> = {
  github: { color: "#238636", emoji: "🐙", label: "GitHub" },
  linear: { color: "#5E6AD2", emoji: "🔷", label: "Linear" },
  notion: { color: "#37352F", emoji: "🗒️", label: "Notion" },
  slack: { color: "#E01E5A", emoji: "💬", label: "Slack" },
};

function sourceFor(source: string) {
  return sourceAccents[source.toLowerCase()] ?? {
    color: tokens.colors.violet,
    emoji: "🛡️",
    label: source || "Source",
  };
}

export function ParticipantPill({ name }: { name: string }) {
  return <Pill username={name} />;
}

export function SourceBadge({ source }: { source: string }) {
  const config = sourceFor(source);

  return (
    <span
      className="inline-flex shrink-0 items-center gap-1.5 rounded-[var(--radius-full)] border px-2.5 py-1 text-[11px] font-extrabold leading-none"
      style={{
        background: `${config.color}12`,
        borderColor: `${config.color}33`,
        color: config.color,
      }}
    >
      <span aria-hidden="true">{config.emoji}</span>
      {config.label}
    </span>
  );
}

export function DecisionCard({ decision, index }: DecisionCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const config = sourceFor(decision.source);

  return (
    <Link
      className="block cursor-pointer"
      href={`/lineage?id=${encodeURIComponent(decision.id)}`}
    >
      <article
        className="overflow-hidden bg-white"
        data-testid="decision-card"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        style={{
          animation: `fadeUp .5s ${index * 0.08}s ease both`,
          animationFillMode: "forwards",
          border: `1.5px solid ${isHovered ? `${config.color}66` : "#E8E8F0"}`,
          borderRadius: tokens.radius.lg,
          boxShadow: isHovered ? `${tokens.shadow.md}, 0 0 0 0 ${config.color}14` : tokens.shadow.sm,
          opacity: 0,
          transition: "all .2s ease",
        }}
      >
        <div
          className="h-[3px]"
          style={{
            background: `linear-gradient(90deg, ${config.color}, ${config.color}66)`,
          }}
        />
        <div className="flex flex-col gap-3 px-4 py-3.5">
          <div className="flex items-start gap-3">
            <h2 className="min-w-0 flex-1 text-sm font-extrabold leading-5 text-[var(--ink)]">
              {decision.summary}
            </h2>
            <SourceBadge source={decision.source} />
          </div>

          <p className="line-clamp-3 text-xs font-medium leading-[1.55] text-[var(--ink-3)]">
            {decision.rationale}
          </p>

          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 flex-wrap gap-1.5">
              {decision.participants.map((participant) => (
                <ParticipantPill key={participant} name={participant} />
              ))}
            </div>
            <span className="shrink-0 text-[11px] font-extrabold text-[var(--ink-4)]">
              {decision.date}
            </span>
          </div>
        </div>
      </article>
    </Link>
  );
}
