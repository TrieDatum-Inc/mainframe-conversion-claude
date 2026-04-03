/**
 * Section header — mirrors BMS neutral-color section title literals.
 * Examples: 'View Account', 'Customer Details', 'Update Account'
 */

import { cn } from "@/lib/utils";

interface SectionHeaderProps {
  title: string;
  className?: string;
}

export function SectionHeader({ title, className }: SectionHeaderProps) {
  return (
    <h2
      className={cn(
        "text-center text-base font-semibold text-gray-600 py-1",
        className
      )}
    >
      {title}
    </h2>
  );
}
