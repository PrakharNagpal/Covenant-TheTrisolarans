// Lane: P3 frontend
import Link from "next/link";
import { AlertTriangle, X } from "lucide-react";
import type { Alert } from "@/lib/api";

type AlertBannerProps = {
  alert?: Alert | null;
  onDismiss?: () => void;
};

export function AlertBanner({ alert, onDismiss }: AlertBannerProps) {
  if (!alert) {
    return null;
  }

  return (
    <div className="sticky top-3 z-50 mx-auto w-full max-w-7xl animate-alert-in px-4 text-[#4B3410] sm:px-6">
      <div className="flex items-center justify-between gap-3 rounded-lg border border-[#D85A30]/70 bg-[#FFF0DD] px-3 py-2 shadow-md ring-1 ring-[#D85A30]/10 sm:px-4">
        <Link
          className="flex min-w-0 flex-1 items-center gap-3"
          href={`/lineage?id=${encodeURIComponent(alert.decision_id)}`}
        >
          <span className="flex h-8 w-8 shrink-0 animate-soft-pulse items-center justify-center rounded-full bg-[#D85A30] text-white">
            <AlertTriangle className="h-4 w-4" />
          </span>
          <span className="min-w-0">
            <span className="block text-[11px] font-bold uppercase leading-4 tracking-wide text-[#A13916]">
              {alert.severity} contradiction detected
            </span>
            <span className="block truncate text-sm font-semibold leading-5 text-[#2B2118] sm:text-base">
              {alert.decision?.summary ?? alert.message}
            </span>
          </span>
        </Link>
        <button
          aria-label="Dismiss alert"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-[#D85A30]/30 text-[#A13916] hover:bg-[#FFE2C2]"
          onClick={onDismiss}
          type="button"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
