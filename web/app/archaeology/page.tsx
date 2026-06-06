// Lane: P3 frontend
"use client";

import { FormEvent, useMemo, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowLeft, Bot, Send, Sparkles, User } from "lucide-react";
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
    <main className="min-h-screen bg-[#F1EFE8] text-[#1B1A22]">
      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-6 px-6 py-8 sm:px-10">
        <header className="flex flex-col gap-6 border-b border-[#D8D2C4] pb-7">
          <Link
            className="inline-flex w-fit items-center gap-2 text-sm font-semibold text-[#534AB7] hover:text-[#453DA0]"
            href="/"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to ledger
          </Link>
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-[#0F6E56]">
              Archaeology Mode
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-[#534AB7] sm:text-4xl">
              Ask why anything looks this way
            </h1>
          </div>
        </header>

        <div className="flex flex-wrap gap-2">
          {quickQuestions.map((question) => (
            <button
              className="inline-flex items-center gap-2 rounded-full border border-[#D8D2C4] bg-white px-4 py-2 text-sm font-semibold text-[#0F6E56] shadow-sm hover:border-[#0F6E56]/40 hover:bg-[#E8F3EE]"
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

        <section className="flex min-h-[420px] flex-1 flex-col gap-4 rounded-lg border border-[#D8D2C4] bg-white p-4 shadow-sm sm:p-6">
          <div className="flex flex-1 flex-col gap-4 overflow-y-auto">
            {messages.map((message) => (
              <ChatBubble key={message.id} message={message} />
            ))}
            {isLoading ? <LoadingBubble /> : null}
          </div>

          <form
            className="flex items-center gap-3 border-t border-[#EEE9DD] pt-4"
            onSubmit={onSubmit}
          >
            <input
              className="min-w-0 flex-1 rounded-lg border border-[#D8D2C4] bg-[#F8F6EF] px-4 py-3 text-sm outline-none focus:border-[#534AB7] focus:bg-white"
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about JWT, checkout, or Postgres"
              value={draft}
            />
            <button
              aria-label="Send question"
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-[#534AB7] text-white shadow-sm hover:bg-[#453DA0] disabled:cursor-not-allowed disabled:bg-[#B7B1D8]"
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
          <Bot className="h-4 w-4" />
        </BubbleIcon>
      ) : null}
      <div
        className={`max-w-[78%] rounded-lg px-4 py-3 text-sm leading-6 ${
          isCovenant
            ? "bg-[#F1EFE8] text-[#1B1A22]"
            : "bg-[#534AB7] text-white"
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
        <Bot className="h-4 w-4" />
      </BubbleIcon>
      <div className="flex items-center gap-2 rounded-lg bg-[#F1EFE8] px-4 py-3">
        <span className="h-2 w-2 animate-bounce rounded-full bg-[#534AB7]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-[#534AB7] [animation-delay:120ms]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-[#534AB7] [animation-delay:240ms]" />
      </div>
    </div>
  );
}

function BubbleIcon({ children }: { children: ReactNode }) {
  return (
    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#E8F3EE] text-[#0F6E56]">
      {children}
    </span>
  );
}
