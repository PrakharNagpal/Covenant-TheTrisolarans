"use client";

import { Button } from "@/components/ui/Button";
import { Pill } from "@/components/ui/Pill";
import { SevBadge } from "@/components/ui/SevBadge";
import { tokens } from "@/lib/tokens";

type AlertBannerProps = {
  onDismiss: () => void;
};

export function AlertBanner({ onDismiss }: AlertBannerProps) {
  return (
    <div
      className="flex items-start gap-3 p-4"
      data-testid="alert-banner"
      style={{
        animation: "slideIn .3s ease",
        background: "linear-gradient(135deg, #FF5C5C15, #F59E0B10)",
        border: "2px solid rgba(255,92,92,0.33)",
        borderRadius: "14px",
        boxShadow: "0 6px 20px rgba(255,92,92,0.12)",
      }}
    >
      <span className="shrink-0 text-[22px] leading-none" aria-hidden="true">
        🛡️
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-extrabold text-[var(--coral)]">
            Promise Check
          </span>
          <SevBadge severity="structural" />
        </div>

        <p className="mt-2 flex flex-wrap items-center gap-1.5 text-[13px] font-medium leading-6 text-[var(--ink-2)]">
          <span>Commit</span>
          <span
            className="rounded-[var(--radius-full)] px-2 py-0.5 font-mono text-[11px] font-bold"
            style={{
              background: tokens.colors.muted,
              color: tokens.colors.ink2,
            }}
          >
            a3f9c12
          </span>
          <span>introduces session-based auth, contradicting the JWT decision by</span>
          <Pill username="@alice" />
          <span className="text-[var(--ink-3)]">· Jan 14</span>
        </p>

        <div className="mt-3 flex flex-wrap gap-2">
          <Button size="sm" variant="coral">
            👍 Intentional
          </Button>
          <Button size="sm" variant="soft">
            View decision
          </Button>
        </div>
      </div>

      <button
        aria-label="Dismiss alert"
        className="shrink-0 rounded-[var(--radius-sm)] px-2 text-xl leading-none text-[var(--ink-3)] transition hover:bg-white/70 hover:text-[var(--coral)]"
        onClick={onDismiss}
        type="button"
      >
        ×
      </button>
    </div>
  );
}
