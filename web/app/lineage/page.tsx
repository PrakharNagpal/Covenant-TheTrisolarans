import { Suspense } from "react";
import type { Metadata } from "next";
import { LineageView } from "@/components/LineageView";

export const metadata: Metadata = {
  title: "Decision Lineage | Covenant",
  description: "Linked artifacts and provenance for Covenant decisions.",
};

export default function LineagePage() {
  return (
    <Suspense fallback={<LineageFallback />}>
      <LineageView />
    </Suspense>
  );
}

function LineageFallback() {
  return (
    <main className="min-h-screen bg-[var(--app-bg)] px-6 py-20">
      <section className="mx-auto max-w-[860px]">
        <div className="h-8 w-36 rounded-full bg-[var(--muted)]" />
        <div className="mt-5 h-48 rounded-[18px] border-[1.5px] border-[var(--border)] bg-[var(--panel)]" />
      </section>
    </main>
  );
}
