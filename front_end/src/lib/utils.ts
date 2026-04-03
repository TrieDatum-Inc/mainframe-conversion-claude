import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as COBOL PIC +99999999.99 display string.
 * Mirrors WS-TRAN-AMT editing in COTRN00C/COTRN01C.
 */
export function formatAmount(amount: number): string {
  const sign = amount >= 0 ? "+" : "-";
  const abs = Math.abs(amount);
  const intPart = Math.floor(abs).toString().padStart(8, "0");
  const fracPart = Math.round((abs % 1) * 100).toString().padStart(2, "0");
  return `${sign}${intPart}.${fracPart}`;
}

/**
 * Format ISO timestamp to MM/DD/YY for list display.
 * Mirrors POPULATE-TRAN-DATA date formatting in COTRN00C.
 */
export function formatDateMMDDYY(isoTimestamp: string): string {
  const d = new Date(isoTimestamp);
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(d.getUTCDate()).padStart(2, "0");
  const yy = String(d.getUTCFullYear()).slice(2);
  return `${mm}/${dd}/${yy}`;
}

/**
 * Format ISO timestamp to display string for detail view.
 * Mirrors TRAN-ORIG-TS / TRAN-PROC-TS verbatim display in COTRN01C.
 */
export function formatTimestamp(isoTimestamp: string): string {
  return new Date(isoTimestamp).toLocaleString();
}

/**
 * Truncate description to 26 characters for list display.
 * Mirrors TDESC field length (col 38, len 26) in COTRN0A.
 */
export function truncateDesc(desc: string, maxLen = 26): string {
  return desc.length > maxLen ? `${desc.slice(0, maxLen - 1)}…` : desc;
}
