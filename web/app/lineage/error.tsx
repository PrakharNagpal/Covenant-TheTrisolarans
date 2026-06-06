// Lane: P3 frontend
"use client";

import Link from "next/link";
import { ArrowLeft, RefreshCw } from "lucide-react";

export default function LineageError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="min-h-screen bg-[#F1EFE8] px-6 py-10 text-[#1B1A22]">
      <section className="mx-auto max-w-3xl rounded-lg border border-[#D85A30] bg-[#FFF0DD] p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-[#A13916]">
          Lineage unavailable
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-[#1B1A22]">
          Could not load this decision lineage
        </h1>
        <p className="mt-3 text-sm leading-6 text-[#6B3C24]">
          {error.message}
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            className="inline-flex items-center gap-2 rounded-lg bg-[#534AB7] px-4 py-2.5 text-sm font-semibold text-white"
            onClick={reset}
            type="button"
          >
            <RefreshCw className="h-4 w-4" />
            Retry
          </button>
          <Link
            className="inline-flex items-center gap-2 rounded-lg border border-[#D8D2C4] bg-white px-4 py-2.5 text-sm font-semibold text-[#534AB7]"
            href="/"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to ledger
          </Link>
        </div>
      </section>
    </main>
  );
}
