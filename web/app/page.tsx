// Lane: P3 frontend
"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { AlertCircle, BookOpen, Database, Radio } from "lucide-react";
import { AlertBanner } from "@/components/AlertBanner";
import { DecisionCard } from "@/components/DecisionCard";
import { useAlerts } from "@/hooks/useAlerts";
import { getDecisions, type Decision } from "@/lib/api";

export default function DecisionLedgerPage() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const { alerts, latestAlert, dismissLatest } = useAlerts();

  useEffect(() => {
    let cancelled = false;

    async function loadDecisions() {
      try {
        const data = await getDecisions();
        if (!cancelled) {
          setDecisions(data);
          setLoadError(null);
        }
      } catch (error) {
        if (!cancelled) {
          setLoadError(
            error instanceof Error
              ? error.message
              : "Could not load decisions.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadDecisions();

    return () => {
      cancelled = true;
    };
  }, []);

  const sourceCount = useMemo(
    () => new Set(decisions.map((decision) => decision.source)).size,
    [decisions],
  );
  const activeAlertIds = useMemo(
    () => new Set(alerts.map((alert) => alert.decision_id)),
    [alerts],
  );

  return (
    <main className="min-h-screen bg-[#F1EFE8] text-[#1B1A22]">
      <AlertBanner alert={latestAlert} onDismiss={dismissLatest} />
      <section className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8 sm:px-10">
        <header className="flex flex-col gap-6 border-b border-[#D8D2C4] pb-7 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-[#0F6E56]">
              Covenant
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-[#534AB7] sm:text-4xl">
              Decision Ledger
            </h1>
            <p className="mt-3 max-w-2xl text-base leading-7 text-[#5D5968]">
              The live memory surface judges keep open: decisions, provenance,
              and contradiction alerts in one scan-friendly view.
            </p>
          </div>
          <Link
            className="inline-flex w-fit items-center gap-2 rounded-lg bg-[#534AB7] px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-[#453DA0]"
            href="/archaeology"
          >
            <BookOpen className="h-4 w-4" />
            Archaeology
          </Link>
        </header>

        <section className="grid gap-3 sm:grid-cols-3">
          <StatTile
            icon={<Database className="h-5 w-5" />}
            label="Decisions"
            value={isLoading ? "..." : String(decisions.length)}
          />
          <StatTile
            icon={<AlertCircle className="h-5 w-5" />}
            label="Alerts today"
            value={String(alerts.length)}
          />
          <StatTile
            icon={<Radio className="h-5 w-5" />}
            label="Sources watching"
            value={isLoading ? "..." : String(sourceCount)}
          />
        </section>

        {isLoading ? (
          <DecisionGridSkeleton />
        ) : loadError ? (
          <DashboardNotice
            tone="error"
            title="Backend is not returning decisions yet"
            text={loadError}
          />
        ) : decisions.length === 0 ? (
          <DashboardNotice
            tone="neutral"
            title="No decisions found"
            text="Seed Supabase or flip mock mode back on to populate the ledger."
          />
        ) : (
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {decisions.map((decision) => (
              <DecisionCard
                decision={decision}
                isFlagged={activeAlertIds.has(decision.id)}
                key={decision.id}
              />
            ))}
          </section>
        )}
      </section>
    </main>
  );
}

function DashboardNotice({
  title,
  text,
  tone,
}: {
  title: string;
  text: string;
  tone: "error" | "neutral";
}) {
  const classes =
    tone === "error"
      ? "border-[#D85A30] bg-[#FFF0DD] text-[#8A2C12]"
      : "border-[#D8D2C4] bg-white text-[#5D5968]";

  return (
    <section className={`rounded-lg border p-6 shadow-sm ${classes}`}>
      <h2 className="text-lg font-semibold text-[#1B1A22]">{title}</h2>
      <p className="mt-2 text-sm leading-6">{text}</p>
    </section>
  );
}

function StatTile({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-4 rounded-lg border border-[#D8D2C4] bg-white px-5 py-4 shadow-sm">
      <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#E8F3EE] text-[#0F6E56]">
        {icon}
      </span>
      <span>
        <span className="block text-2xl font-semibold text-[#1B1A22]">
          {value}
        </span>
        <span className="text-sm font-medium text-[#5D5968]">{label}</span>
      </span>
    </div>
  );
}

function DecisionGridSkeleton() {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          className="h-56 animate-pulse rounded-lg border border-[#D8D2C4] bg-white p-5 shadow-sm"
          key={index}
        >
          <div className="h-5 w-3/4 rounded bg-[#E8E4D8]" />
          <div className="mt-4 h-4 w-full rounded bg-[#EEE9DD]" />
          <div className="mt-2 h-4 w-2/3 rounded bg-[#EEE9DD]" />
          <div className="mt-8 h-px bg-[#EEE9DD]" />
          <div className="mt-5 flex gap-2">
            <div className="h-7 w-16 rounded-full bg-[#E8E4D8]" />
            <div className="h-7 w-20 rounded-full bg-[#E8E4D8]" />
          </div>
        </div>
      ))}
    </section>
  );
}
