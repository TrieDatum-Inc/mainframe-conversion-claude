/**
 * Formatting utilities for display values.
 * Preserves COBOL-era formatting conventions where relevant.
 */

/**
 * Format a decimal string as USD currency.
 * Handles COBOL COMP-3 decimals which arrive as string from API.
 */
export function formatCurrency(value: string | null | undefined): string {
  if (value === null || value === undefined) return '$0.00';
  const num = parseFloat(value);
  if (isNaN(num)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(num);
}

/**
 * Format a date string (YYYY-MM-DD) for display.
 */
export function formatDate(value: string | null | undefined): string {
  if (!value) return '—';
  try {
    const [year, month, day] = value.split('-');
    return `${month}/${day}/${year}`;
  } catch {
    return value;
  }
}

/**
 * Format a card number with spaces every 4 digits.
 * e.g. "4111111111111111" -> "4111 1111 1111 1111"
 */
export function formatCardNumber(cardNum: string | null | undefined): string {
  if (!cardNum) return '—';
  return cardNum.replace(/(.{4})/g, '$1 ').trim();
}

/**
 * Mask a card number showing only last 4 digits.
 * e.g. "4111111111111111" -> "**** **** **** 1111"
 */
export function maskCardNumber(cardNum: string | null | undefined): string {
  if (!cardNum || cardNum.length < 4) return '—';
  const last4 = cardNum.slice(-4);
  return `**** **** **** ${last4}`;
}

/**
 * Format a timestamp string for display.
 */
export function formatTimestamp(value: string | null | undefined): string {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return value;
  }
}

/**
 * Get status badge color for account/card active status.
 */
export function getStatusColor(status: 'Y' | 'N' | null | undefined): string {
  if (status === 'Y') return 'text-green-700 bg-green-50 ring-green-600/20';
  if (status === 'N') return 'text-red-700 bg-red-50 ring-red-600/20';
  return 'text-gray-600 bg-gray-50 ring-gray-500/20';
}

/**
 * Get status label.
 */
export function getStatusLabel(status: 'Y' | 'N' | null | undefined): string {
  if (status === 'Y') return 'Active';
  if (status === 'N') return 'Inactive';
  return 'Unknown';
}

/**
 * Format auth response code for display.
 * '00' = Approved, '05' = Declined
 */
export function formatAuthDecision(code: string | null | undefined): string {
  if (code === '00') return 'Approved';
  if (code === '05') return 'Declined';
  return code ?? '—';
}

/**
 * Uppercase and pad a user ID to match COBOL PIC X(08) behavior.
 */
export function normalizeUserId(userId: string): string {
  return userId.toUpperCase().slice(0, 8);
}

/**
 * Truncate a string with ellipsis.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength - 3)}...`;
}
