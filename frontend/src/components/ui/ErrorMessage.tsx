/**
 * ErrorMessage — maps to ERRMSG field (row 23 on every BMS map).
 *
 * BMS field: ERRMSG (ROW 23, COL 1, LEN 78, ASKIP, BRT, FSET, RED)
 *   ATTRB=(ASKIP,BRT,FSET) — output-only, bright/high-intensity, always transmitted
 *   COLOR=RED — error messages are red
 *
 * COBOL usage:
 *   MOVE 'Error message text' TO ERRMSGO
 *   PERFORM SEND-SCREEN
 *
 * Color variants:
 *   'red'     → DFHRED (error conditions)
 *   'green'   → DFHGREEN (success conditions)
 *   'neutral' → DFHNEUTR (informational)
 */

interface ErrorMessageProps {
  message: string;
  color?: 'red' | 'green' | 'neutral';
}

const COLOR_CLASSES = {
  red: 'bg-red-50 border-red-300 text-red-700',
  green: 'bg-green-50 border-green-300 text-green-700',
  neutral: 'bg-gray-50 border-gray-300 text-gray-600',
} as const;

export function ErrorMessage({ message, color = 'red' }: ErrorMessageProps) {
  if (!message) return null;

  return (
    <div
      className={`px-4 py-2 border font-mono text-sm font-semibold ${COLOR_CLASSES[color]}`}
      role="alert"
      aria-live="polite"
    >
      {message}
    </div>
  );
}
