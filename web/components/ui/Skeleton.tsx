import { tokens } from "@/lib/tokens";

type SkeletonProps = {
  w?: number | string;
  h?: number | string;
  radius?: keyof typeof tokens.radius | string;
};

function sizeValue(value: number | string | undefined, fallback: string) {
  if (typeof value === "number") {
    return `${value}px`;
  }

  return value ?? fallback;
}

export function Skeleton({ w = "100%", h = 16, radius = "md" }: SkeletonProps) {
  const radiusValue = radius in tokens.radius ? tokens.radius[radius as keyof typeof tokens.radius] : radius;

  return (
    <span
      aria-hidden="true"
      className="block"
      style={{
        animation: "shimmer 1.4s linear infinite",
        background: "linear-gradient(90deg, var(--muted) 0%, var(--bg) 50%, var(--muted) 100%)",
        backgroundSize: "600px 100%",
        borderRadius: radiusValue,
        height: sizeValue(h, "16px"),
        width: sizeValue(w, "100%"),
      }}
    />
  );
}
