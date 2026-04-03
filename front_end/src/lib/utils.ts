import { clsx, type ClassValue } from "clsx";
export function cn(...inputs: ClassValue[]): string { return clsx(inputs); }
export function formatExpiry(month: number | null, year: number | null): string {
  if (!month || !year) return "—";
  return `${String(month).padStart(2, "0")}/${year}`;
}
export function extractErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return "An unexpected error occurred";
}
