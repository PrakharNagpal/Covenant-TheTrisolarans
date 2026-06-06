// Lane: P3 frontend
"use client";

import { FormEvent, useMemo, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowLeft, Send, Shield, Sparkles, User } from "lucide-react";
import { ProductTopbar } from "@/components/ProductTopbar";
import { postArchaeology } from "@/lib/api";

type ChatMessage = {
  id: string;
  role: "user" | "covenant";
  text: string;
};

const quickQuestions = [
  "Why are we using JWT?",
  "Why is checkout 3 steps?",
  "Why do we use Postgres?",
];

const openingMessage: ChatMessage = {
  id: "opening",
  role: "covenant",
  text: "Ask why the codebase looks the way it does. I will answer with the people, date, rationale, and rejected alternatives when the decision is recorded.",
};

export default function ArchaeologyPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([openingMessage]);
  const [draft, setDraft] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const canSend = useMemo(
    () => draft.trim().length > 0 && !isLoading,
    [draft, isLoading],
  );

  async function ask(question: string) {
    const trimmed = question.trim();
    if (!trimmed || isLoading) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      text: trimmed,
    };

    setMessages((current) => [...current, userMessage]);
    setDraft("");
    setIsLoading(true);

    try {
      const response = await postArchaeology(trimmed);
      const covenantMessage: ChatMessage = {
        id: `covenant-${Date.now()}`,
        role: "covenant",
        text: response.answer,
      };
      setMessages((current) => [...current, covenantMessage]);
    } catch (error) {
      const covenantMessage: ChatMessage = {
        id: `covenant-error-${Date.now()}`,
        role: "covenant",
        text:
          error instanceof Error
            ? `I could not retrieve that decision yet: ${error.message}`
            : "I could not retrieve that decision yet.",
      };
      setMessages((current) => [...current, covenantMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (canSend) {
      ask(draft);
    }
  }

  return (
    <main className="app-page">
      <ProductTopbar />
      <section className="app-container flex min-h-screen max-w-5xl flex-col gap-6">
        <header className="app-header flex flex-col gap-6">
          <div className="flex items-center justify-between gap-4">
            <Link className="btn-secondary" href="/">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
          </div>
          <div>
            <p className="eyebrow">Archaeology Mode</p>
            <h1 className="page-title mt-2 text-3xl sm:text-4xl">
              Ask why anything looks this way
            </h1>
            <p className="muted mt-2 text-sm font-semibold leading-6">
              New joiner mode: names, dates, rationale, and rejected alternatives.
            </p>
          </div>
        </header>

        <div className="flex flex-wrap gap-2">
          {quickQuestions.map((question) => (
            <button
              className="chip inline-flex items-center gap-2 hover:border-[var(--accent)] hover:bg-[var(--accent-soft)] hover:text-[var(--accent)]"
              disabled={isLoading}
              key={question}
              onClick={() => ask(question)}
              type="button"
            >
              <Sparkles className="h-4 w-4" />
              {question}
            </button>
          ))}
        </div>

        <section className="panel flex min-h-[420px] flex-1 flex-col gap-4 rounded-[18px] p-4 sm:p-6">
          <div className="flex flex-1 flex-col gap-4 overflow-y-auto">
            {messages.map((message) => (
              <ChatBubble key={message.id} message={message} />
            ))}
            {isLoading ? <LoadingBubble /> : null}
          </div>

          <form
            className="flex items-center gap-3 border-t border-[var(--border)] pt-4"
            onSubmit={onSubmit}
          >
            <input
              className="field min-w-0 flex-1 px-4 py-3 text-sm"
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about JWT, checkout, or Postgres"
              value={draft}
            />
            <button
              aria-label="Send question"
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-[var(--button-primary-bg)] text-[var(--button-primary-fg)] shadow-sm hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-45"
              disabled={!canSend}
              type="submit"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </section>
      </section>
    </main>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isCovenant = message.role === "covenant";

  return (
    <div
      className={`flex gap-3 ${isCovenant ? "justify-start" : "justify-end"}`}
    >
      {isCovenant ? (
        <BubbleIcon>
          <Shield className="h-4 w-4" />
        </BubbleIcon>
      ) : null}
      <div
        className={`max-w-[78%] px-4 py-3 text-sm font-medium leading-6 shadow-sm ${
          isCovenant
            ? "rounded-[18px_18px_18px_4px] border-2 border-[color-mix(in_srgb,var(--border)_62%,transparent)] bg-[var(--panel)] text-[var(--text)]"
            : "rounded-[18px_18px_4px_18px] bg-[linear-gradient(135deg,var(--primary),var(--primary-strong))] text-white"
        }`}
      >
        {message.text}
      </div>
      {!isCovenant ? (
        <BubbleIcon>
          <User className="h-4 w-4" />
        </BubbleIcon>
      ) : null}
    </div>
  );
}

function LoadingBubble() {
  return (
    <div className="flex justify-start gap-3">
      <BubbleIcon>
        <Shield className="h-4 w-4" />
      </BubbleIcon>
      <div className="flex items-center gap-2 rounded-lg bg-[var(--panel-soft)] px-4 py-3">
        <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--primary)]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--primary)] [animation-delay:120ms]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--primary)] [animation-delay:240ms]" />
      </div>
    </div>
  );
}

function BubbleIcon({ children }: { children: ReactNode }) {
  return (
    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[linear-gradient(135deg,var(--primary),var(--accent))] text-white shadow-[0_4px_10px_var(--glow-primary)]">
      {children}
    </span>
  );
}
