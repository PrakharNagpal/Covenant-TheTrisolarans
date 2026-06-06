// Lane: P3 frontend
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowDown, Play, Shield, Sparkles } from "lucide-react";

const phrases = [
  "forgets its own decisions.",
  "breaks its own promises.",
  "ignores its own past.",
];

function useTypewriter(speed = 58, pause = 1600) {
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [length, setLength] = useState(0);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const phrase = phrases[phraseIndex];

    if (!deleting && length < phrase.length) {
      const timeout = window.setTimeout(() => setLength((value) => value + 1), speed);
      return () => window.clearTimeout(timeout);
    }

    if (!deleting && length === phrase.length) {
      const timeout = window.setTimeout(() => setDeleting(true), pause);
      return () => window.clearTimeout(timeout);
    }

    if (deleting && length > 0) {
      const timeout = window.setTimeout(
        () => setLength((value) => value - 1),
        speed / 2,
      );
      return () => window.clearTimeout(timeout);
    }

    if (deleting && length === 0) {
      setDeleting(false);
      setPhraseIndex((value) => (value + 1) % phrases.length);
    }
  }, [deleting, length, pause, phraseIndex, speed]);

  return phrases[phraseIndex].slice(0, length);
}

export function ProductHero() {
  const typedText = useTypewriter();

  function scrollToLedger() {
    document.getElementById("ledger")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <section className="hero-shell relative overflow-hidden bg-[var(--hero)] text-white">
      <div className="hero-grid absolute inset-0" />
      <div className="hero-blob hero-blob-violet" />
      <div className="hero-blob hero-blob-mint" />
      <div className="hero-blob hero-blob-coral" />

      <div className="relative z-10 mx-auto flex min-h-[calc(100vh-73px)] max-w-6xl flex-col items-center justify-center px-6 py-20 text-center">
        <div className="hero-fade-up inline-flex items-center gap-3 rounded-full border border-white/15 bg-white/[0.07] px-5 py-3">
          <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-[var(--accent)]" />
          <span className="text-xs font-extrabold uppercase tracking-[0.2em] text-white/55">
            Live · Watching your repo now
          </span>
        </div>

        <h1 className="hero-fade-up mt-14 max-w-6xl text-balance text-[clamp(3rem,7vw,6.2rem)] font-black leading-[0.98] tracking-[-0.07em] text-white [animation-delay:120ms]">
          Every team{" "}
          <span className="hero-gradient-text">
            {typedText}
            <span className="type-cursor ml-1" />
          </span>
        </h1>

        <p className="hero-fade-up mt-8 max-w-4xl text-balance text-xl font-medium leading-9 text-white/42 [animation-delay:220ms] sm:text-2xl">
          Covenant watches your Slack, Notion, GitHub and Linear. The moment code
          contradicts a past decision, it says so.
        </p>

        <div className="hero-fade-up mt-12 flex flex-wrap justify-center gap-5 [animation-delay:320ms]">
          <button
            className="inline-flex items-center gap-3 rounded-2xl bg-[var(--primary)] px-8 py-5 text-lg font-black text-white shadow-[0_22px_44px_rgba(123,108,246,0.24)] transition hover:bg-[var(--primary-strong)]"
            onClick={scrollToLedger}
            type="button"
          >
            <Play className="h-5 w-5 fill-current" />
            Watch it work
          </button>
          <Link
            className="inline-flex items-center gap-3 rounded-2xl border border-white/15 bg-white/[0.06] px-8 py-5 text-lg font-black text-white shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)] transition hover:bg-white/[0.1]"
            href="/archaeology"
          >
            View Design System
            <ArrowDown className="h-5 w-5" />
          </Link>
        </div>

        <div className="hero-fade-in relative mt-28 h-72 w-72">
          <div className="absolute left-1/2 top-1/2 z-10 flex h-28 w-28 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-[2rem] border-[10px] border-[rgba(123,108,246,0.18)] bg-[linear-gradient(135deg,var(--primary),var(--accent))] text-white shadow-[0_0_44px_rgba(123,108,246,0.32)]">
            <Shield className="h-12 w-12" />
          </div>

          <OrbitIcon
            className="hero-orbit-one"
            color="#E01E5A"
            label="Slack"
            text="💬"
          />
          <OrbitIcon
            className="hero-orbit-two"
            color="#37352F"
            label="Notion"
            text="🗒️"
          />
          <OrbitIcon
            className="hero-orbit-three"
            color="#238636"
            label="GitHub"
            text="🐙"
          />
          <OrbitIcon
            className="hero-orbit-four"
            color="#5E6AD2"
            label="Linear"
            text="🔷"
          />
        </div>

        <p className="mt-4 text-sm font-bold tracking-[0.18em] text-white/18">
          Slack · Notion · GitHub · Linear
        </p>
      </div>
    </section>
  );
}

function OrbitIcon({
  className,
  color,
  label,
  text,
}: {
  className: string;
  color: string;
  label: string;
  text: string;
}) {
  return (
    <div
      aria-label={label}
      className={`hero-orbit-icon ${className}`}
      style={{
        background: `${color}22`,
        borderColor: `${color}66`,
      }}
      title={label}
    >
      <span>{text}</span>
      <Sparkles className="absolute -right-1 -top-1 h-3 w-3 text-[var(--primary)] opacity-70" />
    </div>
  );
}
