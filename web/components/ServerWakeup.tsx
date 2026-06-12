"use client";

import { useEffect } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export function ServerWakeup() {
  useEffect(() => {
    fetch(`${API_BASE_URL}/health`, { method: "GET" }).catch(() => {});
  }, []);

  return null;
}
