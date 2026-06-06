"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/Button";

const navLinks = [
  { href: "/", match: "/", emoji: "📚", label: "Decisions" },
  { href: "/archaeology", match: "/archaeology", emoji: "💬", label: "Archaeology" },
  { href: "/lineage?id=d1a2b3c4-0001-4000-a000-000000000001", match: "/lineage", emoji: "🔗", label: "Lineage" },
  { href: "/system-design", match: "/system-design", emoji: "⚙️", label: "System" },
] as const;

export function NavBar() {
  const pathname = usePathname();

  if (pathname === "/") {
    return null;
  }

  return (
    <nav
      className="flex h-14 items-center border-b-[1.5px] border-[#F0F0F5] bg-white px-5"
      style={{ boxShadow: "0 2px 12px rgba(10,10,15,0.04)" }}
    >
      <div className="mx-auto grid w-full max-w-6xl grid-cols-[1fr_auto_1fr] items-center gap-4">
        <Link className="inline-flex items-center gap-2" href="/">
          <span className="flex h-[34px] w-[34px] items-center justify-center rounded-[14px] bg-[linear-gradient(135deg,#7B6CF6,#00C896)] shadow-[var(--shadow-violet)] text-[15px] font-extrabold text-white tracking-tight">
            C
          </span>
          <span className="text-base font-extrabold text-[var(--ink)]">
            Covenant
          </span>
        </Link>

        <div className="hidden items-center gap-1 sm:flex">
          {navLinks.map((link) => {
            const isActive = pathname === link.match;

            return (
              <Link
                className="rounded-[11px] px-4 py-[7px] text-sm"
                href={link.href}
                key={link.label}
                style={{
                  background: isActive ? "var(--violet-lt)" : "transparent",
                  color: isActive ? "var(--violet)" : "var(--ink-3)",
                  fontWeight: isActive ? 700 : 500,
                }}
              >
                <span aria-hidden="true" className="mr-1.5">
                  {link.emoji}
                </span>
                {link.label}
              </Link>
            );
          })}
        </div>

        <div className="flex justify-end">
          <Button size="sm" variant="ghost">
            ⚙️ Settings
          </Button>
        </div>
      </div>
    </nav>
  );
}
