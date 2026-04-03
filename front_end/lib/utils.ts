/**
 * Utility functions for CardDemo frontend.
 */

/**
 * Format a date string for display — mirrors COBOL POPULATE-HEADER-INFO date formatting.
 * COBOL formats as MM/DD/YY; modern format is more readable.
 */
export function formatHeaderDate(isoDate: string): string {
  try {
    const d = new Date(isoDate);
    if (isNaN(d.getTime())) return "";
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const yy = String(d.getFullYear()).slice(2);
    return `${mm}/${dd}/${yy}`;
  } catch {
    return "";
  }
}

/**
 * Format time string — mirrors COBOL HH:MM:SS format in POPULATE-HEADER-INFO.
 */
export function formatHeaderTime(isoDate: string): string {
  try {
    const d = new Date(isoDate);
    if (isNaN(d.getTime())) return "";
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    const ss = String(d.getSeconds()).padStart(2, "0");
    return `${hh}:${mm}:${ss}`;
  } catch {
    return "";
  }
}

/**
 * Extract a readable error message from an API error object.
 */
export function getErrorMessage(error: unknown): string {
  if (!error || typeof error !== "object") return "An unexpected error occurred";
  const e = error as Record<string, unknown>;
  if (typeof e.detail === "string") return e.detail;
  if (typeof e.detail === "object" && e.detail !== null) {
    const d = e.detail as Record<string, unknown>;
    if (typeof d.message === "string") return d.message;
  }
  if (typeof e.message === "string") return e.message;
  return "An unexpected error occurred";
}

/**
 * Map API message_type to Tailwind CSS classes — mirrors COBOL DFHRED/DFHGREEN.
 * DFHRED   → error (red text) — used for error messages on ERRMSG field
 * DFHGREEN → info (green text) — used for "coming soon" / "not installed"
 */
export function messageTypeToClass(
  messageType: "error" | "info" | "success" | null | undefined
): string {
  switch (messageType) {
    case "error":
      return "text-red-600 bg-red-50 border border-red-200";
    case "info":
      return "text-green-700 bg-green-50 border border-green-200";
    case "success":
      return "text-green-800 bg-green-50 border border-green-200";
    default:
      return "text-gray-700 bg-gray-50 border border-gray-200";
  }
}

/** Check if a user is an admin (CDEMO-USRTYP-ADMIN condition). */
export function isAdmin(userType: string): boolean {
  return userType === "A";
}
