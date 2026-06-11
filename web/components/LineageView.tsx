"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import type { Decision, LineageLink } from "@/lib/api";
import { getDecision, getDecisions, getLineage } from "@/lib/api";
import { SourceBadge } from "@/components/DecisionCard";
import { EmptyState } from "@/components/EmptyState";
import { Button } from "@/components/ui/Button";
import { Pill } from "@/components/ui/Pill";
import { Tag } from "@/components/ui/Tag";
import { tokens } from "@/lib/tokens";

const sourceAccents: Record<string, string> = {
  github: "#238636",
  linear: "#5E6AD2",
  notion: "#37352F",
  slack: "#E01E5A",
};

const artifactIcons: Record<string, string> = {
  code: "⌘",
  commit: "⑂",
  file: "📄",
  github_commit: "⑂",
  github_pr: "⑃",
  issue: "▣",
  linear: "◆",
  notion: "▤",
  notion_page: "▤",
  package: "📦",
  pr: "⑃",
  route: "🔀",
  slack: "☷",
  slack_message: "☷",
};

function artifactLabel(type: string) {
  return type.replace(/_/g, " ");
}

function isUrl(value: string) {
  return /^https?:\/\//.test(value);
}

export function LineageView() {
  const searchParams = useSearchParams();
  const requestedId = searchParams.get("id");
  const [decision, setDecision] = useState<Decision | null>(null);
  const [lineage, setLineage] = useState<LineageLink[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadLineage() {
      setIsLoading(true);
      setError(null);

      try {
        let activeId = requestedId;
        if (!activeId) {
          const decisions = await getDecisions();
          activeId = decisions[0]?.id;
        }

        if (!activeId) {
          throw new Error("No decisions are available yet.");
        }

        const [nextDecision, nextLineage] = await Promise.all([
          getDecision(activeId),
          getLineage(activeId),
        ]);

        if (!cancelled) {
          setDecision(nextDecision);
          setLineage(nextLineage);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Could not load this decision lineage.",
          );
          setDecision(null);
          setLineage([]);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadLineage();

    return () => {
      cancelled = true;
    };
  }, [requestedId]);

  const accent = useMemo(
    () => sourceAccents[decision?.source.toLowerCase() ?? ""] ?? tokens.colors.violet,
    [decision],
  );

  return (
    <main className="min-h-[calc(100vh-56px)] bg-[var(--app-bg)] px-6 py-6 text-[var(--ink)] sm:py-8">
      <section className="mx-auto flex max-w-[860px] flex-col gap-3">
        <div>
          <Link href="/">
            <Button size="sm" variant="ghost">
              ← Back to Ledger
            </Button>
          </Link>
        </div>

        <article
          className="relative overflow-hidden bg-[var(--panel)] px-5 py-4 sm:px-6 sm:py-5"
          data-testid="decision-detail-card"
          style={{
            border: "1.5px solid #E8E8F0",
            borderRadius: "18px",
          }}
        >
          <div
            aria-hidden="true"
            className="absolute bottom-5 left-0 top-5 w-[3px] rounded-[99px]"
            style={{ background: accent }}
          />

          {isLoading ? (
            <DetailLoading />
          ) : error ? (
            <div>
              <h1 className="text-[22px] font-extrabold tracking-[-0.5px] text-[var(--ink)]">
                Lineage unavailable
              </h1>
              <p className="mt-2 text-sm leading-[1.65] text-[var(--coral)]">
                {error}
              </p>
            </div>
          ) : decision ? (
            <>
              <h1 className="mb-1.5 text-xl font-extrabold leading-tight tracking-[-0.5px] text-[var(--ink)]">
                {decision.summary}
              </h1>
              <p className="mb-3 line-clamp-4 text-sm font-medium leading-[1.55] text-[var(--ink-3)]">
                {decision.rationale ?? "No rationale has been recorded yet."}
              </p>
              <div className="flex flex-wrap items-center gap-2">
                {decision.participants.map((participant) => (
                  <Pill key={participant} username={participant} />
                ))}
                <Tag color={tokens.colors.ink3} bg={tokens.colors.muted}>
                  {decision.date}
                </Tag>
                <SourceBadge source={decision.source} />
              </div>
            </>
          ) : null}
        </article>

        <div
          aria-hidden="true"
          className="h-px w-full"
          style={{
            background: "linear-gradient(90deg, transparent, #E8E8F0, transparent)",
          }}
        />

        <section>
          <p className="mb-1.5 text-[11px] font-extrabold uppercase tracking-[0.16em] text-[var(--ink-4)]">
            Linked Artifacts
          </p>

          <div data-testid="artifact-list">
            {isLoading ? (
              <ArtifactLoadingRows />
            ) : lineage.length > 0 ? (
              lineage.map((artifact, index) => (
                <ArtifactRow
                  artifact={artifact}
                  isLast={index === lineage.length - 1}
                  key={artifact.id}
                />
              ))
            ) : (
              <EmptyState
                icon="🔗"
                subtitle="Artifacts appear here once the decision is linked to code."
                title="No linked artifacts"
              />
            )}
          </div>
        </section>
      </section>
    </main>
  );
}

function ArtifactRow({
  artifact,
  isLast,
}: {
  artifact: LineageLink;
  isLast: boolean;
}) {
  const normalizedType = artifact.type.toLowerCase();
  const targetContent = (
    <span className="truncate">{artifact.target}</span>
  );

  return (
    <div
      className="flex items-center gap-3 py-2.5"
      data-testid="artifact-row"
      style={{
        borderBottom: isLast ? "none" : "1.5px solid #F5F5F7",
      }}
    >
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[10px] bg-[var(--violet-lt)] text-sm">
        {artifactIcons[normalizedType] ?? "📄"}
      </span>

      <div className="min-w-0 flex-1">
        {isUrl(artifact.target) ? (
          <a
            className="inline-flex max-w-full rounded-[5px] bg-[var(--violet-lt)] px-1.5 py-0.5 font-mono text-[11px] font-extrabold text-[var(--violet)] underline-offset-2 hover:underline"
            href={artifact.target}
            rel="noreferrer"
            target="_blank"
          >
            {targetContent}
          </a>
        ) : (
          <span className="inline-flex max-w-full rounded-[5px] bg-[var(--violet-lt)] px-1.5 py-0.5 font-mono text-[11px] font-extrabold text-[var(--violet)]">
            {targetContent}
          </span>
        )}
        <p className="mt-0.5 text-[11px] font-medium leading-5 text-[var(--ink-3)]">
          {artifact.note ?? "No note recorded."}
        </p>
      </div>

      <Tag color={tokens.colors.violet} bg={tokens.colors.violetLt}>
        {artifactLabel(normalizedType)}
      </Tag>
    </div>
  );
}

function DetailLoading() {
  return (
    <div className="animate-pulse">
      <div className="h-7 w-3/4 rounded-full bg-[var(--muted)]" />
      <div className="mt-3 h-4 w-full rounded-full bg-[var(--muted)]" />
      <div className="mt-2 h-4 w-2/3 rounded-full bg-[var(--muted)]" />
      <div className="mt-4 flex gap-2">
        <div className="h-7 w-16 rounded-full bg-[var(--muted)]" />
        <div className="h-7 w-20 rounded-full bg-[var(--muted)]" />
      </div>
    </div>
  );
}

function ArtifactLoadingRows() {
  return (
    <>
      {[0, 1, 2].map((item) => (
        <div className="flex items-center gap-3 py-2.5" key={item}>
          <div className="h-8 w-8 rounded-[10px] bg-[var(--violet-lt)]" />
          <div className="flex-1">
            <div className="h-4 w-48 rounded-full bg-[var(--muted)]" />
            <div className="mt-2 h-3 w-32 rounded-full bg-[var(--muted)]" />
          </div>
          <div className="h-6 w-14 rounded-full bg-[var(--violet-lt)]" />
        </div>
      ))}
    </>
  );
}
