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

function SlackLogo() {
  return (
    <svg viewBox="0 0 24 24" fill="none" width="26" height="26" aria-hidden="true">
      <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zm1.271 0a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zm2.521-10.123a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zm0 1.271a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zm10.122 2.521a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zm-1.268 0a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zm-2.523 10.122a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zm0-1.268a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" fill="white"/>
    </svg>
  );
}

function NotionLogo() {
  return (
    <svg viewBox="0 0 24 24" fill="white" width="26" height="26" aria-hidden="true">
      <path d="M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 1.968c-.42-.326-.981-.7-2.055-.607L3.01 2.295c-.466.046-.56.28-.374.466zm.793 3.08v13.904c0 .747.373 1.027 1.214.98l14.523-.84c.841-.047.935-.56.935-1.167V6.354c0-.606-.233-.933-.748-.887l-15.177.887c-.56.047-.747.327-.747.933zm14.337.745c.093.42 0 .84-.42.888l-.7.14v10.264c-.608.327-1.168.514-1.635.514-.748 0-.935-.234-1.495-.933l-4.577-7.186v6.952L12.21 19s0 .84-1.168.84l-3.222.186c-.093-.186 0-.653.327-.746l.84-.233V9.854L7.822 9.62c-.094-.42.14-1.026.793-1.073l3.456-.233 4.764 7.279v-6.44l-1.215-.14c-.093-.514.28-.887.747-.933z"/>
    </svg>
  );
}

function GitHubLogo() {
  return (
    <svg viewBox="0 0 24 24" fill="white" width="26" height="26" aria-hidden="true">
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
    </svg>
  );
}

function LinearLogo() {
  return (
    <svg viewBox="0 0 24 24" fill="white" width="26" height="26" aria-hidden="true">
      <path d="M3.368 21.644a.37.37 0 0 1-.525-.525l4.39-4.39A6.27 6.27 0 0 0 8.57 17.9zm-1.03-1.847a.37.37 0 0 1 0-.524l5.15-5.15a6.29 6.29 0 0 0 .745 1.184zm7.97-12.42C7.24 7.377 5.01 10.152 5.01 13.46c0 .42.042.838.12 1.24L15.3 4.528a6.509 6.509 0 0 0-4.993.85zM19.47 5.06 5.772 18.76A6.51 6.51 0 0 0 19.47 5.06zm.958.957A6.51 6.51 0 0 1 6.73 19.714z"/>
    </svg>
  );
}

const orbitItems = [
  { Logo: SlackLogo,  bg: "#4A154B", border: "#611f69", orbitClass: "hero-orbit-one",   label: "Slack"  },
  { Logo: NotionLogo, bg: "#1a1a1a", border: "#333",    orbitClass: "hero-orbit-two",   label: "Notion" },
  { Logo: GitHubLogo, bg: "#161b22", border: "#30363d", orbitClass: "hero-orbit-three", label: "GitHub" },
  { Logo: LinearLogo, bg: "#5E6AD2", border: "#8b93e0", orbitClass: "hero-orbit-four",  label: "Linear" },
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
  window.location.href = "/system-design";
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
              <Link className="transition hover:text-white" href="/system-design">
                System Design
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
                System Design
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
                System Design
              </Button>
            </div>

            <div
              className="relative mx-auto mt-9 h-[300px] w-[300px]"
              style={fadeStyle(5)}
            >
              <div className="absolute left-1/2 top-1/2 z-10 flex h-16 w-16 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-[var(--radius-md)] bg-[linear-gradient(135deg,#7B6CF6,#00C896)] text-2xl shadow-[var(--shadow-violet)] [animation:glow_2.4s_ease-in-out_infinite]">
                <span aria-hidden="true">🛡️</span>
              </div>

              {orbitItems.map((item) => (
                <div
                  aria-label={item.label}
                  className={`hero-orbit-icon ${item.orbitClass} shadow-[0_8px_32px_rgba(0,0,0,0.4)]`}
                  key={item.label}
                  style={{
                    background: item.bg,
                    borderColor: item.border,
                  }}
                  title={item.label}
                >
                  <item.Logo />
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
