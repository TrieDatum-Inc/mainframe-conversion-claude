/**
 * ErrorMessage component — maps BMS ERRMSG field (row 23 on all screens).
 *
 * BMS ERRMSG field attributes: ASKIP, BRT, FSET, color=RED (DFHRED) by default.
 * DFHGREEN is used for "coming soon" / "not installed" messages.
 *
 * Maps COBOL: MOVE WS-MESSAGE TO ERRMSGO OF COMEN1AO
 */
import { messageTypeToClass } from "@/lib/utils";

interface ErrorMessageProps {
  message?: string | null;
  messageType?: "error" | "info" | "success" | null;
}

export function ErrorMessage({ message, messageType = "error" }: ErrorMessageProps) {
  if (!message) return null;

  return (
    <div
      className={`w-full px-4 py-2 rounded font-mono text-sm font-bold ${messageTypeToClass(messageType)}`}
      role="alert"
      aria-live="polite"
    >
      {message}
    </div>
  );
}
