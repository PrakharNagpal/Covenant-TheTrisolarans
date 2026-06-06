import { tokens } from "@/lib/tokens";

type TagProps = {
  children: React.ReactNode;
  color: string;
  bg: string;
};

export function Tag({ children, color, bg }: TagProps) {
  return (
    <span
      className="inline-flex items-center whitespace-nowrap border px-2.5 py-1 text-xs font-bold leading-none"
      style={{
        background: bg,
        borderColor: `${color}33`,
        borderRadius: tokens.radius.full,
        color,
      }}
    >
      {children}
    </span>
  );
}
