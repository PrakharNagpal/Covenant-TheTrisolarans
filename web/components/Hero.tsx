"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Play } from "lucide-react";
import { Button } from "@/components/ui/Button";

const phrases = [
  "breaks its own promises.",
  "forgets its own decisions.",
  "ignores its own past.",
];

const orbitItems = [
  { emoji: "💬", color: "#E01E5A", delay: "0s", label: "Slack" },
  { emoji: "🗒️", color: "#37352F", delay: ".9s", label: "Notion" },
  { emoji: "🐙", color: "#238636", delay: "1.8s", label: "GitHub" },
  { emoji: "🔷", color: "#5E6AD2", delay: "2.7s", label: "Linear" },
] as const;

function useTypewriter() {
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [characterCount, setCharacterCount] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const phrase = phrases[phraseIndex];

    if (!isDeleting && characterCount < phrase.length) {
      const timeout = window.setTimeout(
        () => setCharacterCount((count) => count + 1),
        55,
      );
      return () => window.clearTimeout(timeout);
    }

    if (!isDeleting && characterCount === phrase.length) {
      const timeout = window.setTimeout(() => setIsDeleting(true), 1800);
      return () => window.clearTimeout(timeout);
    }

    if (isDeleting && characterCount > 0) {
      const timeout = window.setTimeout(
        () => setCharacterCount((count) => count - 1),
        28,
      );
      return () => window.clearTimeout(timeout);
    }

    if (isDeleting && characterCount === 0) {
      setIsDeleting(false);
      setPhraseIndex((index) => (index + 1) % phrases.length);
    }
  }, [characterCount, isDeleting, phraseIndex]);

  return phrases[phraseIndex].slice(0, characterCount);
}

function fadeStyle(index: number) {
  return {
    animation: "fadeUp .6s ease forwards",
    animationDelay: `${index * 0.1}s`,
    opacity: 0,
  };
}

function scrollToLedger() {
  document.getElementById("ledger")?.scrollIntoView({ behavior: "smooth" });
}

function openDesignSystem() {
  window.location.href = "/design-test";
}

export function Hero() {
  const typedText = useTypewriter();

  return (
    <section className="relative flex min-h-[680px] overflow-hidden bg-[var(--hero-bg)] text-white md:min-h-[720px]">
      <HeroBackground />

      <div className="relative z-10 flex min-h-[680px] w-full flex-col md:min-h-[720px]">
        <nav
          className="relative border-b border-[rgba(255,255,255,0.06)] px-5 py-3 sm:px-8"
          style={fadeStyle(0)}
        >
          <div className="mx-auto grid max-w-7xl grid-cols-[1fr_auto] items-center gap-4 md:grid-cols-[1fr_auto_1fr]">
            <Link className="inline-flex items-center gap-2 text-white" href="/">
              <span className="text-xl" aria-hidden="true">
                🛡️
              </span>
              <span className="text-base font-extrabold">Covenant</span>
            </Link>

            <div className="hidden items-center gap-8 text-sm font-semibold text-white/[0.55] md:flex">
              <Link className="transition hover:text-white" href="#ledger">
                Decisions
              </Link>
              <Link className="transition hover:text-white" href="/archaeology">
                Archaeology
              </Link>
              <Link className="transition hover:text-white" href="/lineage">
                Lineage
              </Link>
            </div>

            <div className="flex justify-end">
              <Button
                className="hidden sm:inline-flex"
                onClick={openDesignSystem}
                size="sm"
                style={{ color: "rgba(255,255,255,0.72)" }}
                variant="ghost"
              >
                View Design System ↓
              </Button>
            </div>
          </div>
        </nav>

        <div className="flex flex-1 items-center justify-center px-5 py-8 text-center sm:px-8">
          <div className="w-full max-w-[1360px]">
            <div
              className="inline-flex items-center gap-2 rounded-[var(--radius-full)] border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.06)] px-4 py-2"
              style={fadeStyle(1)}
            >
              <span className="h-2.5 w-2.5 rounded-[var(--radius-full)] bg-[var(--mint)] [animation:pulse_1.4s_ease-in-out_infinite]" />
              <span className="text-[11px] font-extrabold uppercase tracking-[0.18em] text-white/[0.55]">
                Live · Watching your repo now
              </span>
            </div>

            <h1
              className="mx-auto mt-6 max-w-[1360px] text-[clamp(36px,6vw,72px)] font-black leading-[1.08] tracking-[-2px] text-white"
              style={fadeStyle(2)}
            >
              Every team{" "}
              <span className="inline-grid align-baseline">
                <span className="invisible col-start-1 row-start-1">
                  breaks its own promises.
                </span>
                <span
                  className="col-start-1 row-start-1 bg-[linear-gradient(90deg,#7B6CF6,#00C896,#F59E0B)] bg-[length:200%_100%] bg-clip-text text-transparent"
                  data-testid="hero-typewriter"
                  style={{
                    animation: "gradMove 4s ease infinite",
                  }}
                >
                  {typedText}
                  <span
                    aria-hidden="true"
                    className="ml-1 inline-block h-[0.9em] translate-y-[0.08em] border-r-[3px]"
                    style={{
                      animation: "typeCursor 1s step-end infinite",
                      borderRightColor: "var(--violet)",
                    }}
                  />
                </span>
              </span>
            </h1>

            <p
              className="mx-auto mt-4 max-w-[480px] text-[17px] font-normal leading-[1.65] text-white/[0.35]"
              style={fadeStyle(3)}
            >
              Covenant watches your Slack, Notion, GitHub and Linear. The moment
              code contradicts a past decision — it says so.
            </p>

            <div
              className="mt-6 flex flex-wrap items-center justify-center gap-3"
              style={fadeStyle(4)}
            >
              <Button
                icon={<Play className="h-4 w-4 fill-current" />}
                onClick={scrollToLedger}
                size="lg"
                variant="primary"
              >
                Watch it work
              </Button>
              <Button onClick={openDesignSystem} size="lg" variant="dark">
                View Design System ↓
              </Button>
            </div>

            <div
              className="relative mx-auto mt-9 h-[160px] w-[160px]"
              style={fadeStyle(5)}
            >
              <div className="absolute left-1/2 top-1/2 z-10 flex h-14 w-14 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-[var(--radius-md)] bg-[linear-gradient(135deg,#7B6CF6,#00C896)] text-2xl shadow-[var(--shadow-violet)] [animation:glow_2.4s_ease-in-out_infinite]">
                <span aria-hidden="true">🛡️</span>
              </div>

              {orbitItems.map((item) => (
                <div
                  aria-label={item.label}
                  className="absolute flex h-9 w-9 items-center justify-center rounded-[var(--radius-md)] border text-lg shadow-[0_10px_28px_rgba(0,0,0,0.28)]"
                  key={item.label}
                  style={{
                    animation: "orbit 7.5s linear infinite",
                    animationDelay: item.delay,
                    background: item.color,
                    borderColor: "rgba(255,255,255,0.18)",
                    left: "calc(50% - 18px)",
                    top: "calc(50% - 18px)",
                  }}
                  title={item.label}
                >
                  <span aria-hidden="true">{item.emoji}</span>
                </div>
              ))}
            </div>

            <p
              className="mt-3 text-sm font-semibold tracking-[0.16em] text-white/[0.14]"
              style={fadeStyle(6)}
            >
              Slack · Notion · GitHub · Linear
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function HeroBackground() {
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0">
      <svg className="absolute inset-0 h-full w-full opacity-[0.04]">
        <defs>
          <pattern
            height="60"
            id="hero-grid"
            patternUnits="userSpaceOnUse"
            width="60"
          >
            <path
              d="M 60 0 L 0 0 0 60"
              fill="none"
              stroke="white"
              strokeWidth="0.5"
            />
          </pattern>
        </defs>
        <rect fill="url(#hero-grid)" height="100%" width="100%" />
      </svg>

      <div className="absolute left-[15%] top-[20%] h-[360px] w-[360px] -translate-x-1/2 -translate-y-1/2 rounded-[var(--radius-full)] bg-[radial-gradient(circle,rgba(123,108,246,0.28),transparent_68%)] blur-xl" />
      <div className="absolute left-[75%] top-[60%] h-[390px] w-[390px] -translate-x-1/2 -translate-y-1/2 rounded-[var(--radius-full)] bg-[radial-gradient(circle,rgba(0,200,150,0.22),transparent_68%)] blur-xl" />
      <div className="absolute left-[85%] top-[10%] h-[300px] w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-[var(--radius-full)] bg-[radial-gradient(circle,rgba(255,92,92,0.18),transparent_68%)] blur-xl" />
      <div className="absolute left-[5%] top-[75%] h-[330px] w-[330px] -translate-x-1/2 -translate-y-1/2 rounded-[var(--radius-full)] bg-[radial-gradient(circle,rgba(245,158,11,0.16),transparent_68%)] blur-xl" />
    </div>
  );
}
