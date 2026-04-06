"use client";

import { formatCurrency } from "@/lib/utils";

interface CurrencyDisplayProps {
  amount: number;
  className?: string;
}

export function CurrencyDisplay({ amount, className = "" }: CurrencyDisplayProps) {
  const isNegative = amount < 0;
  return (
    <span
      className={`font-mono ${
        isNegative ? "text-mainframe-error" : "text-mainframe-text"
      } ${className}`}
    >
      {formatCurrency(amount)}
    </span>
  );
}
