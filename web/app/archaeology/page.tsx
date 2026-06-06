import type { Metadata } from "next";
import { ArchaeologyChat } from "@/components/ArchaeologyChat";

export const metadata: Metadata = {
  title: "Archaeology | Covenant",
  description: "Ask Covenant about institutional memory and past decisions.",
};

export default function ArchaeologyPage() {
  return <ArchaeologyChat />;
}
