// Lane: P3 frontend
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getAlerts, type Alert } from "@/lib/api";

export function useAlerts() {
  const [latestAlert, setLatestAlert] = useState<Alert | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const sinceRef = useRef<string | null>(null);
  const seenIdsRef = useRef<Set<string>>(new Set());

  const dismissLatest = useCallback(() => {
    setLatestAlert(null);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function pollAlerts() {
      try {
        const alerts = await getAlerts(sinceRef.current);
        console.log("[Covenant] useAlerts poll", alerts);

        if (alerts.length > 0) {
          const newest = alerts[0];
          sinceRef.current = newest.created_at ?? new Date().toISOString();
          if (!cancelled) {
            setAlerts((current) => {
              const known = new Set(current.map((alert) => alert.id));
              const fresh = alerts.filter((alert) => !known.has(alert.id));
              return [...fresh, ...current].slice(0, 12);
            });

            if (!seenIdsRef.current.has(newest.id)) {
              seenIdsRef.current.add(newest.id);
              setLatestAlert(newest);
            }
          }
        }
      } catch (error) {
        console.error("[Covenant] useAlerts failed", error);
      }
    }

    pollAlerts();
    const interval = window.setInterval(pollAlerts, 3000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  return { alerts, latestAlert, dismissLatest };
}
