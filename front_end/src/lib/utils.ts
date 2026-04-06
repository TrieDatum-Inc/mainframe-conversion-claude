/**
 * Shared utility functions.
 */

/** Format a number as USD currency. */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(amount);
}

/** Format expiration as MM/YYYY. */
export function formatExpiry(month?: number, year?: number): string {
  if (!month || !year) return "N/A";
  return `${String(month).padStart(2, "0")}/${year}`;
}

/** Pad a string to a fixed width (COBOL PIC X right-pad equivalent). */
export function padRight(value: string, length: number): string {
  return value.padEnd(length, " ").slice(0, length);
}

/** Convert YYYY-MM-DD to MM/DD/YYYY for display. */
export function formatDate(isoDate?: string): string {
  if (!isoDate) return "";
  const [year, month, day] = isoDate.split("-");
  return `${month}/${day}/${year}`;
}
