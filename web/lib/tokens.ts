export const tokens = {
  colors: {
    violet: "#7B6CF6",
    violetDk: "#5B4ED8",
    violetLt: "#EEECFF",
    mint: "#00C896",
    coral: "#FF5C5C",
    amber: "#F59E0B",
    sky: "#38BDF8",
    rose: "#F472B6",
    sage: "#4ADE80",
    peach: "#FB923C",
    ink: "#0A0A0F",
    ink2: "#3A3A4A",
    ink3: "#8E8EA0",
    ink4: "#C8C8D8",
    bg: "#FFFFFF",
    muted: "#F5F5F7",
    heroBg: "#08080E",
  },
  radius: {
    sm: "8px",
    md: "12px",
    lg: "16px",
    xl: "20px",
    full: "9999px",
  },
  shadow: {
    sm: "0 2px 8px rgba(10,10,15,0.06)",
    md: "0 12px 32px rgba(10,10,15,0.10)",
    violet: "0 4px 16px rgba(123,108,246,0.30)",
  },
  source: {
    slack: {
      color: "#F472B6",
      bg: "#FFF0F8",
      emoji: "💬",
      label: "Slack",
    },
    notion: {
      color: "#4ADE80",
      bg: "#F0FDF4",
      emoji: "📝",
      label: "Notion",
    },
    github: {
      color: "#38BDF8",
      bg: "#F0F9FF",
      emoji: "🐙",
      label: "GitHub",
    },
    linear: {
      color: "#FB923C",
      bg: "#FFF7ED",
      emoji: "◆",
      label: "Linear",
    },
  },
  severity: {
    structural: {
      color: "#FF5C5C",
      bg: "#FFF5F5",
      label: "Structural",
    },
    behavioural: {
      color: "#F59E0B",
      bg: "#FFFBEB",
      label: "Behavioural",
    },
    cosmetic: {
      color: "#7B6CF6",
      bg: "#F5F3FF",
      label: "Cosmetic",
    },
  },
  participantColors: [
    "#7B6CF6",
    "#00C896",
    "#FF5C5C",
    "#F59E0B",
    "#38BDF8",
    "#F472B6",
    "#4ADE80",
    "#FB923C",
  ],
} as const;

export type Tokens = typeof tokens;
export type SourceKey = keyof typeof tokens.source;
export type SeverityKey = keyof typeof tokens.severity;
export type ButtonVariant = "primary" | "ghost" | "soft" | "coral" | "mint" | "dark";
export type ButtonSize = "sm" | "md" | "lg";
