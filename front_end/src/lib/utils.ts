import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a user type code as a human-readable label.
 * Maps BMS hint "(A=Admin, U=User)" from COUSR01/02/03 BMS maps.
 */
export function formatUserType(userType: string): string {
  switch (userType) {
    case 'A':
      return 'Admin';
    case 'U':
      return 'User';
    default:
      return userType;
  }
}

/**
 * Extract a readable error message from an API error or unknown value.
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
}
