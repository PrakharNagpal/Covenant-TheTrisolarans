"use client";

import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { postArchaeology } from "@/lib/api";

type ChatMessage = {
  id: string;
  role: "user" | "covenant";
  text: string;
};

const quickQuestions = [
  "Why are we using JWT?",
  "Why is checkout 3 steps?",
  "Why Postgres?",
];

const greeting: ChatMessage = {
  id: "greeting",
  role: "covenant",
  text: "Ask me about a decision and I will trace it back to the people, date, and reason your team recorded.",
};

export function ArchaeologyChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([greeting]);
  const [draft, setDraft] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const isMounted = useRef(true);

  const canSend = useMemo(
    () => draft.trim().length > 0 && !isLoading,
    [draft, isLoading],
  );

  useEffect(() => {
    listRef.current?.scrollTo({
      behavior: "smooth",
      top: listRef.current.scrollHeight,
    });
  }, [messages, isLoading]);

  useEffect(() => {
    isMounted.current = true;

    return () => {
      isMounted.current = false;
    };
  }, []);

  async function sendQuestion(question: string) {
    const trimmed = question.trim();
    if (!trimmed || isLoading) {
      return;
    }

    setMessages((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        role: "user",
        text: trimmed,
      },
    ]);
    setDraft("");
    setIsLoading(true);

    try {
      const [response] = await Promise.all([
        postArchaeology(trimmed),
        new Promise((resolve) => window.setTimeout(resolve, 1200)),
      ]);

      if (!isMounted.current) {
        return;
      }

      setMessages((current) => [
        ...current,
        {
          id: `covenant-${Date.now()}`,
          role: "covenant",
          text: response.answer,
        },
      ]);
    } catch (error) {
      console.error("[Covenant] archaeology failed", error);
      if (!isMounted.current) {
        return;
      }
      setMessages((current) => [
        ...current,
        {
          id: `covenant-${Date.now()}`,
          role: "covenant",
          text: "I could not reach the archaeology service just now. Try again once the API is running.",
        },
      ]);
    } finally {
      if (!isMounted.current) {
        return;
      }
      setIsLoading(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (canSend) {
      sendQuestion(draft);
    }
  }

  function onInputKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" && canSend) {
      event.preventDefault();
      sendQuestion(draft);
    }
  }

  return (
    <main className="min-h-[calc(100vh-56px)] bg-[#F8F8FC] px-6 py-6 sm:py-8">
      <section className="mx-auto flex max-w-[580px] flex-col items-center">
        <header className="mb-4 text-center">
          <div className="mb-2 text-[26px]" aria-hidden="true">
            💬
          </div>
          <h2 className="text-[28px] font-extrabold leading-tight tracking-[-0.8px] text-[var(--ink)]">
            Ask Covenant anything
          </h2>
          <p className="mt-1.5 text-[15px] font-medium text-[var(--ink-3)]">
            Why does the codebase look the way it does? Ask.
          </p>
        </header>

        <section
          className="flex h-[340px] w-full flex-col overflow-hidden bg-white sm:h-[380px]"
          data-testid="archaeology-chat"
          style={{
            border: "1.5px solid #E8E8F0",
            borderRadius: "20px",
            boxShadow: "0 8px 40px rgba(10,10,15,0.06)",
          }}
        >
          <div className="flex items-center border-b border-[#E8E8F0] bg-[linear-gradient(90deg,rgba(123,108,246,0.05),rgba(0,200,150,0.05))] px-[18px] py-3">
            <div className="flex gap-1.5">
              <span className="h-2.5 w-2.5 rounded-[var(--radius-full)] bg-[var(--coral)]" />
              <span className="h-2.5 w-2.5 rounded-[var(--radius-full)] bg-[var(--amber)]" />
              <span className="h-2.5 w-2.5 rounded-[var(--radius-full)] bg-[var(--mint)]" />
            </div>
            <span className="ml-2 text-xs font-extrabold text-[var(--ink-4)]">
              Covenant Archaeology
            </span>
          </div>

          <div
            className="flex flex-1 flex-col gap-2.5 overflow-y-auto px-[18px] py-3.5"
            data-testid="message-list"
            ref={listRef}
          >
            {messages.map((message) => (
              <ChatBubble key={message.id} message={message} />
            ))}
            {isLoading ? <TypingIndicator /> : null}
          </div>

          <div className="flex flex-wrap gap-[7px] px-4 pb-2">
            {quickQuestions.map((question) => (
              <button
                className="rounded-[99px] border-[1.5px] border-[var(--violet-lt)] bg-[var(--muted)] px-3 py-1.5 text-[11px] font-extrabold text-[var(--violet)] hover:bg-[var(--violet-lt)] disabled:opacity-50"
                disabled={isLoading}
                key={question}
                onClick={() => sendQuestion(question)}
                type="button"
              >
                {question}
              </button>
            ))}
          </div>

          <form
            className="border-t-[1.5px] border-[#F0F0F5] px-4 py-2.5"
            onSubmit={onSubmit}
          >
            <div className="flex items-center gap-2 rounded-[var(--radius-md)] border-[1.5px] border-[#E8E8F0] bg-[var(--muted)] px-3 py-2">
              <input
                className="min-w-0 flex-1 bg-transparent text-[13px] font-medium text-[var(--ink)] outline-none placeholder:text-[var(--ink-4)]"
                data-testid="archaeology-input"
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={onInputKeyDown}
                placeholder="Ask about JWT, checkout, or Postgres"
                value={draft}
              />
              <Button disabled={!canSend} size="sm" type="submit" variant="primary">
                ↑
              </Button>
            </div>
          </form>
        </section>
      </section>
    </main>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : "flex-row"} items-end`}
      data-testid={isUser ? "user-bubble" : "covenant-bubble"}
    >
      {!isUser ? <CovenantAvatar /> : null}
      <div
        className="max-w-[76%] px-3.5 py-2.5 text-[13px] font-medium leading-[1.65]"
        style={{
          animation: "pop .3s ease",
          background: isUser ? "var(--violet)" : "var(--muted)",
          borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
          boxShadow: isUser ? "0 4px 14px rgba(123,108,246,0.30)" : "none",
          color: isUser ? "#fff" : "var(--ink)",
        }}
      >
        {message.text}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex flex-row items-end gap-2.5" data-testid="typing-indicator">
      <CovenantAvatar />
      <div
        className="flex items-center gap-1.5 px-3.5 py-3"
        style={{
          animation: "pop .3s ease",
          background: "var(--muted)",
          borderRadius: "16px 16px 16px 4px",
        }}
      >
        {[0, 0.22, 0.44].map((delay) => (
          <span
            className="h-[7px] w-[7px] rounded-[var(--radius-full)] bg-[var(--violet)]"
            key={delay}
            style={{
              animation: "pulse 1s ease-in-out infinite",
              animationDelay: `${delay}s`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

function CovenantAvatar() {
  return (
    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[var(--radius-full)] bg-[linear-gradient(135deg,#7B6CF6,#00C896)] text-sm">
      🛡️
    </span>
  );
}
