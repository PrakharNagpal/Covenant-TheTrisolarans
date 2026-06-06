"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getAlerts, type Alert } from "@/lib/api";
import { mockAlerts } from "@/lib/mock";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "1";

export function useAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const lastSeenRef = useRef<string | null>(null);
  const dismissedRef = useRef<Set<string>>(new Set());

  const dismiss = useCallback((id: string) => {
    dismissedRef.current.add(id);
    setAlerts((current) => current.filter((alert) => alert.id !== id));
  }, []);

  useEffect(() => {
    let cancelled = false;
    let mockTimer: number | null = null;

    async function pollAlerts() {
      try {
        const nextAlerts = await getAlerts(lastSeenRef.current);
        if (cancelled) {
          return;
        }

        const visibleAlerts = nextAlerts.filter(
          (alert) => !dismissedRef.current.has(alert.id),
        );

        if (visibleAlerts.length > 0) {
          lastSeenRef.current =
            visibleAlerts[0].created_at ?? new Date().toISOString();
          setAlerts((current) => {
            const known = new Set(current.map((alert) => alert.id));
            const fresh = visibleAlerts.filter((alert) => !known.has(alert.id));
            return [...fresh, ...current].slice(0, 12);
          });
        }
      } catch (error) {
        console.error("[Covenant] useAlerts failed", error);
      }
    }

    if (USE_MOCK) {
      setAlerts([]);
      mockTimer = window.setTimeout(() => {
        if (!cancelled) {
          const alert = mockAlerts[0];
          if (alert && !dismissedRef.current.has(alert.id)) {
            setAlerts([alert]);
          }
        }
      }, 5000);
    } else {
      pollAlerts();
      const interval = window.setInterval(pollAlerts, 3000);

      return () => {
        cancelled = true;
        window.clearInterval(interval);
      };
    }

    return () => {
      cancelled = true;
      if (mockTimer) {
        window.clearTimeout(mockTimer);
      }
    };
  }, []);

  return { alerts, dismiss };
}
