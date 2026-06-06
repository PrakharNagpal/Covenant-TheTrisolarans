"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertBanner } from "@/components/AlertBanner";
import { DecisionCard } from "@/components/DecisionCard";
import { EmptyState } from "@/components/EmptyState";
import { Hero } from "@/components/Hero";
import { LiveDemo } from "@/components/LiveDemo";
import { SkeletonCard } from "@/components/SkeletonCard";
import { Button } from "@/components/ui/Button";
import { useAlerts } from "@/hooks/useAlerts";
import { getDecisions, type Decision } from "@/lib/api";

const filters = ["All", "Slack", "Notion", "GitHub", "Linear"] as const;

export function DecisionLedger() {
  const [activeFilter, setActiveFilter] = useState<(typeof filters)[number]>("All");
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showSimulatedAlert, setShowSimulatedAlert] = useState(false);
  const { alerts, dismiss } = useAlerts();
  const activeAlert = alerts[0];

  useEffect(() => {
    let cancelled = false;

    async function loadDecisions() {
      setIsLoading(true);
      try {
        const nextDecisions = await getDecisions();
        if (!cancelled) {
          setDecisions(nextDecisions);
        }
      } catch (error) {
        console.error("[Covenant] decisions failed", error);
        if (!cancelled) {
          setDecisions([]);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadDecisions();

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredDecisions = useMemo(() => {
    if (activeFilter === "All") {
      return decisions;
    }

    return decisions.filter(
      (decision) => decision.source.toLowerCase() === activeFilter.toLowerCase(),
    );
  }, [activeFilter, decisions]);

  const showBanner = Boolean(activeAlert) || showSimulatedAlert;

  return (
    <main className="min-h-screen bg-[var(--bg)] text-[var(--ink)]">
      <Hero />
      <LiveDemo />

      <section className="mx-auto max-w-[860px] px-6 py-12" id="ledger">
        <header className="mb-5 text-center">
          <p className="text-[11px] font-extrabold uppercase tracking-[0.2em] text-[var(--mint)]">
            Decision Ledger
          </p>
          <h1 className="mt-2 text-3xl font-extrabold tracking-[-0.02em] text-[var(--ink)]">
            Team memory, ready for review
          </h1>
          <p className="mx-auto mt-2 max-w-xl text-sm font-medium leading-6 text-[var(--ink-3)]">
            Filter the source trail, inspect past decisions, and simulate the promise check banner.
          </p>
        </header>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-2">
            {filters.map((filter) => (
              <Button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                size="sm"
                variant={activeFilter === filter ? "primary" : "soft"}
              >
                {filter}
              </Button>
            ))}
          </div>

          <Button size="sm" variant="ghost">
            🔍 Search
          </Button>
        </div>

        {showBanner ? (
          <div className="mt-4">
            <AlertBanner
              onDismiss={() => {
                if (activeAlert) {
                  dismiss(activeAlert.id);
                }
                setShowSimulatedAlert(false);
              }}
            />
          </div>
        ) : null}

        <section
          className="mt-4 grid gap-3"
          data-testid="decision-grid"
          style={{
            gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          }}
        >
          {isLoading ? (
            Array.from({ length: 6 }).map((_, index) => (
              <SkeletonCard key={index} />
            ))
          ) : filteredDecisions.length > 0 ? (
            filteredDecisions.map((decision, index) => (
              <DecisionCard decision={decision} index={index} key={decision.id} />
            ))
          ) : (
            <div className="col-span-full">
              <EmptyState
                icon="🛡️"
                subtitle="Start a conversation in #eng-decisions or push a commit."
                title="No decisions yet"
              />
            </div>
          )}
        </section>

        <div className="mt-5 flex justify-center">
          <Button onClick={() => setShowSimulatedAlert(true)} variant="ghost">
            Simulate alert ↑
          </Button>
        </div>
      </section>
    </main>
  );
}
