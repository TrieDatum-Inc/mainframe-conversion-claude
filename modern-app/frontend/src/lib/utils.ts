/**
 * Shared frontend utility functions.
 */
import type { UserType } from "@/types";

/** Human-readable label for a user type code. */
export function userTypeLabel(userType: UserType): string {
  return userType === "A" ? "Admin" : "User";
}

/** Format an ISO date string to a readable local date. */
export function formatDate(isoString: string): string {
  if (!isoString) return "";
  return new Date(isoString).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** Truncate a string to maxLen characters, appending ellipsis if cut. */
export function truncate(value: string, maxLen: number): string {
  if (value.length <= maxLen) return value;
  return value.slice(0, maxLen - 1) + "…";
}

/** Build a display name from first and last name. */
export function fullName(firstName: string, lastName: string): string {
  return `${firstName} ${lastName}`.trim();
}
