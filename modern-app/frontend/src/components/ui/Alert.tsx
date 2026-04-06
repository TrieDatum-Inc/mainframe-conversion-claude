"use client";

import { cn } from "@/lib/utils";

interface AlertProps {
  variant?: "error" | "success" | "info" | "warning";
  title?: string;
  message: string;
  className?: string;
}

const variantMap = {
  error: {
    container: "bg-red-50 border-red-300 text-red-800",
    title: "text-red-900",
  },
  success: {
    container: "bg-green-50 border-green-300 text-green-800",
    title: "text-green-900",
  },
  info: {
    container: "bg-blue-50 border-blue-300 text-blue-800",
    title: "text-blue-900",
  },
  warning: {
    container: "bg-amber-50 border-amber-300 text-amber-800",
    title: "text-amber-900",
  },
};

export function Alert({ variant = "info", title, message, className }: AlertProps) {
  const styles = variantMap[variant];
  return (
    <div
      role="alert"
      className={cn(
        "rounded-lg border px-4 py-3 text-sm",
        styles.container,
        className
      )}
    >
      {title && <p className={cn("font-semibold mb-1", styles.title)}>{title}</p>}
      <p>{message}</p>
    </div>
  );
}
