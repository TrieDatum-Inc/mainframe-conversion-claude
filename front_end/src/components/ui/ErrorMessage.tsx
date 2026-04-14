"use client";

/**
 * ErrorMessage — full-width status/error message bar.
 *
 * COBOL origin: ERRMSG field on every BMS map (row 23, ASKIP,BRT,FSET,RED).
 * The original field was 78 characters wide, displayed in bright red when
 * an error occurred. The modern equivalent is a styled alert bar.
 *
 * Color variants match BMS programmatic colors:
 *   red     → DFHRED (error conditions)
 *   green   → DFHGREEN (success confirmations)
 *   neutral → DFHNEUTR (informational messages)
 */

interface ErrorMessageProps {
  message: string;
  color?: "red" | "green" | "neutral";
}

const colorClasses: Record<NonNullable<ErrorMessageProps["color"]>, string> = {
  red: "bg-red-50 border-red-200 text-red-700",
  green: "bg-green-50 border-green-200 text-green-700",
  neutral: "bg-slate-50 border-slate-200 text-slate-700",
};

export function ErrorMessage({ message, color = "red" }: ErrorMessageProps) {
  if (!message) return null;

  return (
    <div
      role="alert"
      aria-live="polite"
      className={`w-full px-4 py-3 rounded-md border text-sm font-medium ${colorClasses[color]}`}
    >
      {message}
    </div>
  );
}
