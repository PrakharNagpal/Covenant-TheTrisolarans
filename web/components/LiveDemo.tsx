"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Pill } from "@/components/ui/Pill";
import { SevBadge } from "@/components/ui/SevBadge";
import { tokens } from "@/lib/tokens";

const pipelineSteps = [
  {
    id: "commit",
    icon: "📦",
    label: "Commit pushed",
    sub: "001-session-auth.patch",
    color: "#7B6CF6",
  },
  {
    id: "webhook",
    icon: "⚡",
    label: "Webhook received",
    sub: "/webhooks/github → 200ms",
    color: "#F59E0B",
  },
  {
    id: "diff",
    icon: "🔍",
    label: "Diff extracted",
    sub: "7 files · +234 −12 lines",
    color: "#38BDF8",
  },
  {
    id: "ai",
    icon: "🧠",
    label: "AI checking…",
    sub: "gpt-4o · 10 decisions",
    color: "#00C896",
  },
  {
    id: "alert",
    icon: "🛡️",
    label: "Contradiction found!",
    sub: "structural · confidence 0.96",
    color: "#FF5C5C",
  },
] as const;

type StepState = "idle" | "active" | "done";

export function LiveDemo() {
  const [activeStep, setActiveStep] = useState(-1);
  const [done, setDone] = useState(false);
  const [running, setRunning] = useState(false);
  const timers = useRef<number[]>([]);

  function clearTimers() {
    timers.current.forEach((timer) => window.clearTimeout(timer));
    timers.current = [];
  }

  function runPipeline() {
    clearTimers();
    setRunning(true);
    setDone(false);
    setActiveStep(-1);

    pipelineSteps.forEach((_, index) => {
      const timer = window.setTimeout(() => {
        setActiveStep(index);
      }, 900 * (index + 1));
      timers.current.push(timer);
    });

    const completeTimer = window.setTimeout(
      () => {
        setDone(true);
        setRunning(false);
      },
      900 * pipelineSteps.length + 600,
    );
    timers.current.push(completeTimer);
  }

  useEffect(() => clearTimers, []);

  return (
    <section
      data-testid="live-demo"
      className="relative overflow-hidden bg-[#0D0D18] px-5 py-14 text-white sm:px-8"
      style={{
        backgroundImage:
          "radial-gradient(circle, rgba(255,255,255,0.06) 1px, transparent 1px)",
        backgroundSize: "28px 28px",
      }}
    >
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-7">
        <header className="max-w-3xl text-center">
          <p className="text-[11px] font-extrabold uppercase tracking-[0.2em] text-[var(--violet)]">
            Interactive Demo
          </p>
          <h2 className="mt-2 text-4xl font-extrabold tracking-[-0.02em] text-white">
            Watch Covenant catch a broken promise
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-white/[0.27]">
            A commit lands, Covenant traces it against team memory, and the PR gets a promise check.
          </p>
        </header>

        <div className="w-full overflow-x-auto pb-1">
          <div className="mx-auto flex w-max min-w-full items-center justify-center px-1">
            {pipelineSteps.map((step, index) => {
              const state = stateForStep(index, activeStep, done);

              return (
                <div className="flex items-center" key={step.id}>
                  <PipelineNode state={state} step={step} />
                  {index < pipelineSteps.length - 1 ? (
                    <Connector passed={activeStep > index || done} />
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex min-h-10 items-center justify-center gap-3">
          {!running && !done ? (
            <Button onClick={runPipeline} size="lg" variant="primary">
              ▶ Push commit & watch
            </Button>
          ) : null}

          {running ? (
            <Button disabled size="lg" variant="soft">
              ⏳ Running…
            </Button>
          ) : null}

          {done ? (
            <>
              <Button onClick={runPipeline} size="lg" variant="mint">
                ↺ Run again
              </Button>
              <Button size="lg" variant="soft">
                See the PR →
              </Button>
            </>
          ) : null}
        </div>

        {done ? <PrCommentCard /> : null}
      </div>
    </section>
  );
}

function stateForStep(index: number, activeStep: number, done: boolean): StepState {
  if (done || activeStep > index) {
    return "done";
  }

  if (activeStep === index) {
    return "active";
  }

  return "idle";
}

function PipelineNode({
  state,
  step,
}: {
  state: StepState;
  step: (typeof pipelineSteps)[number];
}) {
  const isActive = state === "active";
  const isDone = state === "done";

  return (
    <div
      className="flex min-w-[96px] flex-col items-center gap-1.5 border px-3.5 py-3 text-center"
      data-testid={`pipeline-node-${step.id}`}
      style={{
        background: isActive
          ? `${step.color}22`
          : isDone
            ? "rgba(255,255,255,0.08)"
            : "rgba(255,255,255,0.04)",
        borderColor: isActive
          ? `${step.color}66`
          : isDone
            ? "rgba(255,255,255,0.16)"
            : "rgba(255,255,255,0.06)",
        borderRadius: tokens.radius.lg,
        boxShadow: isActive ? `0 0 24px ${step.color}33` : "none",
        transform: isActive ? "scale(1.06)" : "scale(1)",
        transition: "background .4s ease, border-color .4s ease, box-shadow .4s ease, transform .4s ease",
      }}
    >
      <span
        className="flex h-8 w-8 items-center justify-center text-lg"
        style={{
          filter: state === "idle" ? "grayscale(1)" : "none",
          opacity: state === "idle" ? 0.38 : 1,
        }}
      >
        {isDone ? "✓" : step.icon}
      </span>
      <span
        className="max-w-[96px] text-[11px] font-extrabold leading-4"
        style={{
          color: isActive
            ? step.color
            : isDone
              ? "rgba(255,255,255,0.4)"
              : "rgba(255,255,255,0.2)",
        }}
      >
        {step.label}
      </span>
      <span className="max-w-[110px] font-mono text-[9px] leading-4 text-white/20">
        {step.sub}
      </span>
    </div>
  );
}

function Connector({ passed }: { passed: boolean }) {
  return (
    <span
      aria-hidden="true"
      className="mx-2 h-0.5 w-5 rounded-[var(--radius-full)] transition-colors duration-300"
      style={{
        background: passed ? "rgba(255,255,255,0.3)" : "rgba(255,255,255,0.1)",
      }}
    />
  );
}

function PrCommentCard() {
  return (
    <article
      data-testid="pr-comment-card"
      className="w-full max-w-2xl overflow-hidden bg-white text-[var(--ink)]"
      style={{
        animation: "pop .4s cubic-bezier(.16,1,.3,1)",
        border: "2px solid rgba(255,92,92,0.27)",
        borderRadius: tokens.radius.lg,
        boxShadow: "0 20px 60px #FF5C5C22",
      }}
    >
      <header className="flex flex-wrap items-center gap-2 border-b border-[#FF5C5C22] bg-[#FF5C5C0A] px-4 py-3">
        <span className="text-lg" aria-hidden="true">
          🛡️
        </span>
        <span className="mr-auto text-sm font-extrabold text-[var(--coral)]">
          Covenant — Promise Check
        </span>
        <span className="rounded-[var(--radius-full)] bg-[var(--muted)] px-2.5 py-1 font-mono text-[10px] font-bold text-[var(--ink-2)]">
          7f3a9c1
        </span>
        <SevBadge severity="structural" />
      </header>

      <div className="flex flex-col gap-3 p-4">
        <p className="text-[13px] font-extrabold text-[var(--ink)]">
          ⚠️ This change may break a promise your team made.
        </p>

        <div
          className="border-l-[3px] bg-[#F8F8FC] p-3.5"
          style={{
            borderColor: tokens.colors.violet,
            borderRadius: "10px",
          }}
        >
          <p className="text-[11px] font-extrabold text-[var(--violet)]">
            Past decision — Jan 14, 2025
          </p>
          <p className="mt-1.5 text-[13px] font-semibold leading-6 text-[var(--ink-2)]">
            Use JWT for all auth. Stateless, works for mobile, no shared session store.
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Pill username="@alice" />
            <Pill username="@bob" />
          </div>
        </div>

        <div
          className="border-l-[3px] bg-[#FFF5F5] p-3.5 text-[13px] font-semibold leading-6 text-[var(--ink-2)]"
          style={{
            borderColor: "#EF4444",
            borderRadius: "10px",
          }}
        >
          This commit introduces session-based auth, directly contradicting the JWT decision.
          Confidence: 96%
        </div>

        <div className="flex flex-wrap gap-2 pt-0.5">
          <Button size="sm" variant="coral">
            👍 Intentional override
          </Button>
          <Button size="sm" variant="soft">
            View in Covenant →
          </Button>
        </div>
      </div>
    </article>
  );
}
