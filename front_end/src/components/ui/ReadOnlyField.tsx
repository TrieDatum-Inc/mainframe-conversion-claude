/**
 * Read-only display field — equivalent to BMS ASKIP/PROT fields.
 * Used throughout the Account View screen (COACTVWC CACTVWA map).
 */

import { cn } from "@/lib/utils";
import { Label } from "./Label";

interface ReadOnlyFieldProps {
  label: string;
  value: string | number | null | undefined;
  className?: string;
  valueClassName?: string;
  underline?: boolean; // mirrors BMS HILIGHT=UNDERLINE
}

export function ReadOnlyField({
  label,
  value,
  className,
  valueClassName,
  underline = true,
}: ReadOnlyFieldProps) {
  const display = value !== null && value !== undefined ? String(value) : "";
  return (
    <div className={cn("flex flex-col gap-0.5", className)}>
      <Label className="text-xs text-cyan-700">{label}</Label>
      <span
        className={cn(
          "block min-h-[1.5rem] px-1 py-0.5 text-sm text-gray-800",
          underline && "border-b border-gray-400",
          valueClassName
        )}
      >
        {display || "\u00A0"}
      </span>
    </div>
  );
}
