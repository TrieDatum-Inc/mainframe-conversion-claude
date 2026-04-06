/**
 * CurrencyDisplay component.
 *
 * COBOL origin: Replaces PICOUT='+ZZZ,ZZZ,ZZZ.99' output picture on CACTVWA map.
 * The COBOL PICOUT format shows sign, comma-separated thousands, and 2 decimal places.
 * Uses Intl.NumberFormat for locale-aware currency formatting with explicit sign display.
 *
 * Example: -1234.56 → "-$1,234.56" | 10000.00 → "+$10,000.00"
 */

'use client';

interface CurrencyDisplayProps {
  /** Amount as string (from API Decimal) or number */
  amount: string | number;
  /** Show explicit + sign for positive values (matches COBOL PICOUT '+ZZZ...' format) */
  showSign?: boolean;
  /** CSS class override */
  className?: string;
}

/**
 * Format a numeric value with currency formatting.
 * Matches COBOL PICOUT='+ZZZ,ZZZ,ZZZ.99' behavior.
 */
export function formatCurrency(amount: string | number, showSign = true): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '$0.00';

  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    signDisplay: showSign ? 'always' : 'auto',
  }).format(num);

  return formatted;
}

export default function CurrencyDisplay({
  amount,
  showSign = true,
  className = '',
}: CurrencyDisplayProps) {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  const isNegative = !isNaN(num) && num < 0;

  return (
    <span
      className={`font-mono ${isNegative ? 'text-red-600' : 'text-green-700'} ${className}`}
      aria-label={`Currency amount: ${formatCurrency(amount, showSign)}`}
    >
      {formatCurrency(amount, showSign)}
    </span>
  );
}
