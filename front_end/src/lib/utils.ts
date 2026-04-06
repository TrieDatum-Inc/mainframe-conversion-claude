/**
 * Utility functions for formatting and display.
 * Maps COBOL MOVE/COMPUTE formatting operations to TypeScript.
 */

/**
 * Format currency amount for display.
 * Replaces: COBOL PIC -zzzzzzz9.99 (WS-AUTH-AMT formatting in COPAUS0C/1C).
 */
export function formatCurrency(amount: number | string): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(num);
}

/**
 * Format date from ISO string to MM/DD/YY display format.
 * Replaces: COPAUS0C WS-AUTH-DATE PIC X(08) formatted as MM/DD/YY (PDATEnn field).
 */
export function formatAuthDate(dateStr: string): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const yy = String(d.getFullYear()).slice(-2);
    return `${mm}/${dd}/${yy}`;
  } catch {
    return dateStr;
  }
}

/**
 * Format time from ISO string to HH:MM:SS display format.
 * Replaces: COPAUS0C WS-AUTH-TIME PIC X(08) formatted as HH:MM:SS (PTIMEnn field).
 */
export function formatAuthTime(timeStr: string): string {
  if (!timeStr) return '';
  // Handle time-only string "HH:MM:SS"
  if (/^\d{2}:\d{2}:\d{2}/.test(timeStr)) {
    return timeStr.substring(0, 8);
  }
  // Handle ISO datetime string
  try {
    const d = new Date(timeStr);
    return d.toTimeString().substring(0, 8);
  } catch {
    return timeStr;
  }
}

/**
 * Combine class names conditionally.
 * Used throughout the component library.
 */
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

/**
 * Get approval status label and color.
 * Replaces: COPAUS0C WS-AUTH-APRV-STAT ('A'=green, 'D'=red).
 */
export function getApprovalConfig(status: 'A' | 'D'): {
  label: string;
  className: string;
} {
  return status === 'A'
    ? { label: 'Approved', className: 'text-green-700 font-semibold' }
    : { label: 'Declined', className: 'text-red-600 font-semibold' };
}

/**
 * Get match status label.
 * Replaces: COPAUS1C AUTHMTCO field — P/D/E/M displayed in RED on COPAU01.
 */
export function getMatchStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    P: 'Pending',
    D: 'Declined',
    E: 'Expired',
    M: 'Matched',
  };
  return labels[status] ?? status;
}

/**
 * Truncate text to a max length with ellipsis.
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
}
