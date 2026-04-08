/**
 * Status badge component.
 */
import React from 'react';
import { cn } from '@/lib/utils/cn';

interface StatusBadgeProps {
  status: 'Y' | 'N' | string | null | undefined;
  activeLabel?: string;
  inactiveLabel?: string;
  className?: string;
}

export function StatusBadge({
  status,
  activeLabel = 'Active',
  inactiveLabel = 'Inactive',
  className,
}: StatusBadgeProps) {
  const isActive = status === 'Y';
  const label = status === 'Y' ? activeLabel : status === 'N' ? inactiveLabel : status ?? 'Unknown';

  return (
    <span
      className={cn(
        'badge',
        isActive
          ? 'text-green-700 bg-green-50 ring-green-600/20'
          : status === 'N'
          ? 'text-red-700 bg-red-50 ring-red-600/20'
          : 'text-gray-600 bg-gray-50 ring-gray-500/20',
        className
      )}
    >
      {label}
    </span>
  );
}

interface AuthBadgeProps {
  isApproved: boolean;
  className?: string;
}

export function AuthBadge({ isApproved, className }: AuthBadgeProps) {
  return (
    <span
      className={cn(
        'badge',
        isApproved
          ? 'text-green-700 bg-green-50 ring-green-600/20'
          : 'text-red-700 bg-red-50 ring-red-600/20',
        className
      )}
    >
      {isApproved ? 'Approved' : 'Declined'}
    </span>
  );
}
