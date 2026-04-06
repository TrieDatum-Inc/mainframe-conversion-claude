/**
 * Utility functions for the CardDemo frontend.
 * Provides formatting helpers that replace COBOL PICOUT and date/time operations.
 */

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind CSS classes with conflict resolution.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as currency.
 *
 * COBOL origin: Replaces PICOUT='+ZZZ,ZZZ,ZZZ.99' format used on
 * account balance and transaction amount fields.
 */
export function formatCurrency(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined) return '$0.00';
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    signDisplay: 'auto',
  }).format(num);
}

/**
 * Format a date string as MM/DD/YY (CURDATEO field format).
 *
 * COBOL origin: CURDATEO BMS field shows date in MM/DD/YY format.
 */
export function formatDateMMDDYY(dateStr: string | null | undefined): string {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const year = String(date.getFullYear()).slice(-2);
    return `${month}/${day}/${year}`;
  } catch {
    return dateStr;
  }
}

/**
 * Format a date as YYYY-MM-DD for display.
 */
export function formatDateISO(dateStr: string | null | undefined): string {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toISOString().slice(0, 10);
  } catch {
    return dateStr ?? '';
  }
}

/**
 * Mask a card number for display.
 *
 * COBOL origin: CARD-NUM X(16) stored in VSAM — PCI requires masking.
 * Produces format: 411111XXXXXX1111
 */
export function maskCardNumber(cardNumber: string | null | undefined): string {
  if (!cardNumber) return '';
  if (cardNumber.length !== 16) return cardNumber;
  return `${cardNumber.slice(0, 6)}XXXXXX${cardNumber.slice(-4)}`;
}

/**
 * Get user type display label.
 *
 * COBOL: SEC-USR-TYPE 'A'=Admin, 'U'=User
 */
export function getUserTypeLabel(userType: 'A' | 'U' | string): string {
  return userType === 'A' ? 'Admin' : 'User';
}
