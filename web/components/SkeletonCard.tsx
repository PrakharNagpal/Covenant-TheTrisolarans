import { Skeleton } from "@/components/ui/Skeleton";
import { tokens } from "@/lib/tokens";

export function SkeletonCard() {
  return (
    <article
      className="overflow-hidden bg-white"
      data-testid="skeleton-card"
      style={{
        border: "1.5px solid #E8E8F0",
        borderRadius: tokens.radius.lg,
        boxShadow: tokens.shadow.sm,
      }}
    >
      <div
        className="h-[3px]"
        style={{
          animation: "shimmer 1.4s linear infinite",
          background:
            "linear-gradient(90deg, var(--muted) 0%, var(--violet-lt) 45%, var(--muted) 100%)",
          backgroundSize: "600px 100%",
        }}
      />
      <div className="flex flex-col gap-3 px-4 py-3.5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton h={16} radius="full" />
            <Skeleton w="72%" h={16} radius="full" />
          </div>
          <Skeleton w={68} h={24} radius="full" />
        </div>
        <div className="flex flex-col gap-2">
          <Skeleton h={12} radius="full" />
          <Skeleton w="80%" h={12} radius="full" />
        </div>
        <div className="flex items-center justify-between gap-3">
          <div className="flex gap-2">
            <Skeleton w={64} h={24} radius="full" />
            <Skeleton w={58} h={24} radius="full" />
          </div>
          <Skeleton w={42} h={12} radius="full" />
        </div>
      </div>
    </article>
  );
}
