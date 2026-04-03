import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format a monetary value as a display string with sign and commas. */
export function formatCurrency(value: number): string {
  const sign = value < 0 ? "-" : value === 0 ? " " : "+";
  const abs = Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${sign}${abs}`;
}

/** Format a date string (ISO) as MM/DD/YYYY for display. */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  const d = new Date(dateStr + "T00:00:00");
  if (isNaN(d.getTime())) return dateStr;
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const yyyy = d.getFullYear();
  return `${mm}/${dd}/${yyyy}`;
}

/** Parse (aaa)bbb-cccc phone string into parts for the form. */
export function parsePhone(phone: string | null): {
  area_code: string;
  prefix: string;
  line_number: string;
} | null {
  if (!phone) return null;
  const match = phone.match(/^\((\d{3})\)(\d{3})-(\d{4})$/);
  if (!match) return null;
  return { area_code: match[1], prefix: match[2], line_number: match[3] };
}

/** Parse 9-digit SSN into three parts for the form. */
export function parseSsn(ssn: string | null): {
  part1: string;
  part2: string;
  part3: string;
} | null {
  if (!ssn) return null;
  const digits = ssn.replace(/\D/g, "").padStart(9, "0");
  if (digits.length < 9) return null;
  return { part1: digits.slice(0, 3), part2: digits.slice(3, 5), part3: digits.slice(5, 9) };
}
