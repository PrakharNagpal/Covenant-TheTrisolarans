import { tokens } from "@/lib/tokens";

type PillProps = {
  username: string;
};

function colorForUsername(username: string) {
  let hash = 0;
  for (const character of username) {
    hash = (hash * 31 + character.charCodeAt(0)) % tokens.participantColors.length;
  }

  return tokens.participantColors[hash];
}

function initialForUsername(username: string) {
  return username.replace(/^@/, "").trim().slice(0, 1).toUpperCase() || "?";
}

export function Pill({ username }: PillProps) {
  const color = colorForUsername(username);

  return (
    <span
      className="inline-flex items-center gap-1.5 border px-1 py-0.5 pr-2 text-xs font-bold leading-none"
      style={{
        background: `${color}14`,
        borderColor: `${color}33`,
        borderRadius: tokens.radius.full,
        color,
      }}
    >
      <span
        className="inline-flex h-5 w-5 items-center justify-center text-[10px] font-extrabold text-white"
        style={{
          background: color,
          borderRadius: tokens.radius.full,
        }}
      >
        {initialForUsername(username)}
      </span>
      {username}
    </span>
  );
}
