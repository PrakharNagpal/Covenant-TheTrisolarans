"use client";

import { useMemo, useState } from "react";
import { AlertBanner } from "@/components/AlertBanner";
import { DecisionCard } from "@/components/DecisionCard";
import { Hero } from "@/components/Hero";
import { LiveDemo } from "@/components/LiveDemo";
import { SkeletonCard } from "@/components/SkeletonCard";
import { Button } from "@/components/ui/Button";
import { mockDecisions } from "@/lib/mock";

const filters = ["All", "Slack", "Notion", "GitHub", "Linear"] as const;

export default function DecisionLedgerPage() {
  const [activeFilter, setActiveFilter] = useState<(typeof filters)[number]>("All");
  const [showAlert, setShowAlert] = useState(false);

  const decisions = useMemo(() => {
    if (activeFilter === "All") {
      return mockDecisions;
    }

    return mockDecisions.filter(
      (decision) => decision.source.toLowerCase() === activeFilter.toLowerCase(),
    );
  }, [activeFilter]);

  return (
    <main className="min-h-screen bg-[var(--bg)] text-[var(--ink)]">
      <Hero />
      <LiveDemo />

      <section className="mx-auto max-w-[860px] px-6 py-20" id="ledger">
        <header className="mb-8 text-center">
          <p className="text-[11px] font-extrabold uppercase tracking-[0.2em] text-[var(--mint)]">
            Decision Ledger
          </p>
          <h1 className="mt-3 text-4xl font-extrabold tracking-[-0.02em] text-[var(--ink)]">
            Team memory, ready for review
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-sm font-medium leading-6 text-[var(--ink-3)]">
            Filter the source trail, inspect past decisions, and simulate the promise check banner.
          </p>
        </header>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
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

        {showAlert ? (
          <div className="mt-5">
            <AlertBanner onDismiss={() => setShowAlert(false)} />
          </div>
        ) : null}

        <section
          className="mt-5 grid gap-[14px]"
          data-testid="decision-grid"
          style={{
            gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          }}
        >
          {decisions.map((decision, index) => (
            <DecisionCard decision={decision} index={index} key={decision.id} />
          ))}
          <SkeletonCard />
          <SkeletonCard />
        </section>

        <div className="mt-8 flex justify-center">
          <Button onClick={() => setShowAlert(true)} variant="ghost">
            Simulate alert ↑
          </Button>
        </div>
      </section>
    </main>
  );
}
