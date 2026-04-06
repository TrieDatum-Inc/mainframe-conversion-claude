/**
 * Shared utility functions for the frontend.
 */

import { clsx, type ClassValue } from "clsx";

/** Tailwind class merging utility. */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

/**
 * Format a numeric amount for display.
 * Positive amounts are credits (green), negative are debits (red).
 */
export function formatAmount(amount: number): string {
  const abs = Math.abs(amount);
  const sign = amount >= 0 ? "+" : "-";
  return `${sign}${abs.toFixed(2)}`;
}

/** Return Tailwind color classes for an amount (green=credit, red=debit). */
export function amountColorClass(amount: number): string {
  return amount >= 0 ? "text-green-600" : "text-red-600";
}

/** Format a date string (ISO or datetime) as MM/DD/YYYY. */
export function formatDate(dateStr: string): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString("en-US", {
    month: "2-digit",
    day: "2-digit",
    year: "numeric",
  });
}

/** Extract the YYYY-MM-DD portion from a datetime string. */
export function toIsoDate(datetimeStr: string): string {
  return datetimeStr.split("T")[0];
}

/** Truncate a string and append ellipsis if too long. */
export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen - 1) + "…";
}

/** Build a human-readable error message from an API error. */
export function getErrorMessage(error: unknown): string {
  if (!error) return "An unknown error occurred";
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;
  const e = error as { response?: { data?: { detail?: unknown } }; message?: string };
  const detail = e.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message: string }).message);
  }
  return e.message ?? "Request failed";
}
