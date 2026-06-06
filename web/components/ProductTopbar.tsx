// Lane: P3 frontend
import Link from "next/link";
import { Shield } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

export function ProductTopbar() {
  return (
    <nav className="border-b border-white/10 bg-[var(--hero)] px-6 py-4 text-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
        <Link className="flex items-center gap-3" href="/">
          <span className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-[linear-gradient(135deg,var(--primary),var(--accent))] shadow-[0_4px_14px_var(--glow-primary)]">
            <Shield className="h-5 w-5" />
          </span>
          <span className="text-base font-black tracking-[-0.03em]">
            Covenant
          </span>
          <span className="hidden rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold text-white/60 sm:inline-flex">
            Live · Watching demo repo
          </span>
        </Link>
        <div className="hidden items-center gap-7 text-sm font-semibold text-white/50 md:flex">
          <Link className="hover:text-white" href="/">
            Decisions
          </Link>
          <Link className="hover:text-white" href="/archaeology">
            Archaeology
          </Link>
          <Link className="hover:text-white" href="/lineage?id=dec-001">
            Lineage
          </Link>
        </div>
        <ThemeToggle />
      </div>
    </nav>
  );
}
