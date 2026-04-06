/**
 * Utility functions for authorization module.
 */

/**
 * Format a decimal string as currency. e.g. "12345.67" → "$12,345.67"
 */
export function formatCurrency(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "$0.00";
  const num = typeof value === "string" ? parseFloat(value) : value;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num);
}

/**
 * Format a date string. e.g. "2026-04-01" → "04/01/2026"
 */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  const [year, month, day] = dateStr.split("-");
  return `${month}/${day}/${year}`;
}

/**
 * Format a time string. e.g. "10:23:45" → "10:23:45"
 */
export function formatTime(timeStr: string | null | undefined): string {
  if (!timeStr) return "";
  return timeStr.substring(0, 8);
}

/**
 * Mask a card number showing only last 4 digits.
 * e.g. "4111111111111111" → "**** **** **** 1111"
 */
export function maskCardNumber(cardNumber: string): string {
  if (!cardNumber || cardNumber.length < 4) return cardNumber;
  const last4 = cardNumber.slice(-4);
  return `**** **** **** ${last4}`;
}

/**
 * Return Tailwind CSS classes for the auth response badge.
 * Approved = green, Declined = red.
 */
export function getResponseBadgeClasses(response: string): string {
  return response === "A"
    ? "bg-green-100 text-green-800 border border-green-300"
    : "bg-red-100 text-red-800 border border-red-300";
}

/**
 * Return Tailwind CSS classes for the fraud status badge.
 * Fraud confirmed (F) = red. Fraud removed (R) = yellow. Null = gray.
 */
export function getFraudBadgeClasses(fraudStatus: string | null): string {
  if (fraudStatus === "F") return "bg-red-100 text-red-900 border border-red-400 font-bold";
  if (fraudStatus === "R") return "bg-yellow-100 text-yellow-800 border border-yellow-300";
  return "bg-gray-100 text-gray-600 border border-gray-200";
}

/**
 * Return Tailwind CSS classes for match status badges.
 */
export function getMatchStatusClasses(matchStatus: string): string {
  const classes: Record<string, string> = {
    P: "bg-blue-100 text-blue-800",
    D: "bg-red-100 text-red-800",
    E: "bg-gray-100 text-gray-600",
    M: "bg-green-100 text-green-800",
  };
  return classes[matchStatus] ?? "bg-gray-100 text-gray-600";
}

/**
 * Return Tailwind CSS classes for account status.
 */
export function getAccountStatusClasses(authStatus: string): string {
  return authStatus === "A"
    ? "text-green-700 font-semibold"
    : "text-red-700 font-semibold";
}
