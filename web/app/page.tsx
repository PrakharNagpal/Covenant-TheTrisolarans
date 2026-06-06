import type { Metadata } from "next";
import { DecisionLedger } from "@/components/DecisionLedger";

export const metadata: Metadata = {
  title: "Decision Ledger | Covenant",
  description: "Team memory and promise checks for Covenant.",
};

export default function HomePage() {
  return <DecisionLedger />;
}
