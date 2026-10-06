import type { ButtonHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md";

const BASE =
  "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors disabled:opacity-50";

const VARIANTS: Record<ButtonVariant, string> = {
  primary: "bg-slate-900 text-white enabled:hover:bg-slate-700",
  secondary:
    "border border-slate-300 bg-white text-slate-700 enabled:hover:bg-slate-100",
  ghost: "text-slate-600 enabled:hover:bg-slate-100 enabled:hover:text-slate-900",
  danger: "bg-red-600 text-white enabled:hover:bg-red-700",
};

const SIZES: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`${BASE} ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    />
  );
}

export function TextButton({
  className = "",
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type={type}
      className={`text-sm text-slate-500 hover:text-slate-900 hover:underline ${className}`}
      {...props}
    />
  );
}

type IconButtonTone = "neutral" | "danger";

const ICON_TONES: Record<IconButtonTone, string> = {
  neutral: "enabled:hover:bg-slate-100 enabled:hover:text-slate-900",
  danger: "enabled:hover:bg-red-50 enabled:hover:text-red-600",
};

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  tone?: IconButtonTone;
}

export function IconButton({
  tone = "neutral",
  className = "",
  type = "button",
  ...props
}: IconButtonProps) {
  return (
    <button
      type={type}
      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-slate-400 transition-colors disabled:opacity-50 ${ICON_TONES[tone]} ${className}`}
      {...props}
    />
  );
}
