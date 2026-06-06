import { Bell, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Divider } from "@/components/ui/Divider";
import { Pill } from "@/components/ui/Pill";
import { SevBadge } from "@/components/ui/SevBadge";
import { Skeleton } from "@/components/ui/Skeleton";
import { SourceBadge } from "@/components/ui/SourceBadge";
import { Tag } from "@/components/ui/Tag";
import { tokens } from "@/lib/tokens";

export default function DesignTestPage() {
  return (
    <main className="min-h-screen bg-[var(--bg)] px-6 py-10 text-[var(--ink)]">
      <section className="mx-auto flex max-w-3xl flex-col gap-6">
        <div>
          <p className="text-sm font-bold uppercase text-[var(--mint)]">Covenant</p>
          <h1 className="mt-2 text-3xl font-extrabold">Primitive Component Test</h1>
        </div>

        <Divider />

        <div className="flex flex-wrap items-center gap-3">
          <Tag color={tokens.colors.violet} bg={tokens.colors.violetLt}>
            Decision
          </Tag>
          <Pill username="@ada" />
          <SourceBadge source="slack" />
          <SevBadge severity="structural" />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button icon={<Bell className="h-4 w-4" />}>Primary</Button>
          <Button variant="ghost" size="sm">
            Ghost
          </Button>
          <Button variant="soft">Soft</Button>
          <Button variant="coral">Coral</Button>
          <Button variant="mint" icon={<CheckCircle className="h-4 w-4" />}>
            Mint
          </Button>
          <Button variant="dark" size="lg">
            Dark
          </Button>
          <Button disabled>Disabled</Button>
        </div>

        <div className="grid gap-3 rounded-[var(--radius-md)] bg-[var(--muted)] p-4">
          <Skeleton h={18} radius="full" />
          <Skeleton w="72%" h={18} radius="full" />
          <Skeleton w={180} h={40} radius="sm" />
        </div>
      </section>
    </main>
  );
}
