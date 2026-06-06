"use client";

import { useState } from "react";
import type { CSSProperties } from "react";
import { tokens, type ButtonSize, type ButtonVariant } from "@/lib/tokens";

type ButtonProps = {
  children: React.ReactNode;
  className?: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: React.ReactNode;
  disabled?: boolean;
  onClick?: React.ButtonHTMLAttributes<HTMLButtonElement>["onClick"];
  style?: CSSProperties;
  type?: React.ButtonHTMLAttributes<HTMLButtonElement>["type"];
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-5 text-base",
};

const variantStyles: Record<
  ButtonVariant,
  {
    background: string;
    borderColor: string;
    color: string;
    hoverBackground: string;
    hoverBorderColor: string;
    shadow?: string;
  }
> = {
  primary: {
    background: tokens.colors.violet,
    borderColor: tokens.colors.violet,
    color: tokens.colors.bg,
    hoverBackground: tokens.colors.violetDk,
    hoverBorderColor: tokens.colors.violetDk,
    shadow: tokens.shadow.violet,
  },
  ghost: {
    background: "transparent",
    borderColor: "transparent",
    color: tokens.colors.ink2,
    hoverBackground: tokens.colors.muted,
    hoverBorderColor: tokens.colors.muted,
  },
  soft: {
    background: tokens.colors.violetLt,
    borderColor: tokens.colors.violetLt,
    color: tokens.colors.violetDk,
    hoverBackground: "color-mix(in srgb, var(--violet-lt) 86%, var(--violet))",
    hoverBorderColor: "color-mix(in srgb, var(--violet-lt) 86%, var(--violet))",
  },
  coral: {
    background: tokens.colors.coral,
    borderColor: tokens.colors.coral,
    color: tokens.colors.bg,
    hoverBackground: "color-mix(in srgb, var(--coral) 88%, var(--ink))",
    hoverBorderColor: "color-mix(in srgb, var(--coral) 88%, var(--ink))",
  },
  mint: {
    background: tokens.colors.mint,
    borderColor: tokens.colors.mint,
    color: tokens.colors.ink,
    hoverBackground: "color-mix(in srgb, var(--mint) 88%, var(--ink))",
    hoverBorderColor: "color-mix(in srgb, var(--mint) 88%, var(--ink))",
  },
  dark: {
    background: tokens.colors.ink,
    borderColor: tokens.colors.ink,
    color: tokens.colors.bg,
    hoverBackground: tokens.colors.ink2,
    hoverBorderColor: tokens.colors.ink2,
  },
};

export function Button({
  children,
  className = "",
  variant = "primary",
  size = "md",
  icon,
  disabled = false,
  onClick,
  style,
  type = "button",
}: ButtonProps) {
  const [isHovered, setIsHovered] = useState(false);
  const config = variantStyles[variant];
  const activeBackground = isHovered && !disabled ? config.hoverBackground : config.background;
  const activeBorder = isHovered && !disabled ? config.hoverBorderColor : config.borderColor;

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 border font-bold leading-none transition disabled:opacity-45 ${sizeStyles[size]} ${className}`}
      disabled={disabled}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        background: activeBackground,
        borderColor: activeBorder,
        borderRadius: tokens.radius.sm,
        boxShadow: disabled ? "none" : config.shadow,
        color: config.color,
        ...style,
      }}
      type={type}
    >
      {icon ? <span className="inline-flex h-4 w-4 items-center justify-center">{icon}</span> : null}
      {children}
    </button>
  );
}
