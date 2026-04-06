'use client';

/**
 * MessageBar component — maps to ERRMSGO field (row 23 on every BMS map).
 *
 * COBOL origin: ERRMSG ASKIP BRT FSET in all COUSR maps.
 * Color variant matches DFHRED / DFHGREEN / DFHNEUTR programmatic attributes:
 *   DFHRED   → variant='error'   → red background  (validation failures)
 *   DFHGREEN → variant='success' → green background (successful operations)
 *   DFHNEUTR → variant='info'    → gray background  (neutral prompts)
 */

import React from 'react';

interface MessageBarProps {
  message: string;
  variant?: 'error' | 'success' | 'info';
  className?: string;
}

export function MessageBar({ message, variant = 'info', className = '' }: MessageBarProps) {
  if (!message) return null;

  const variantClasses = {
    // DFHRED — error messages: COUSR01C field validation failures, NOT FOUND errors
    error: 'bg-red-50 border-red-300 text-red-700',
    // DFHGREEN — success messages: 'User [ID] has been added ...', 'deleted successfully'
    success: 'bg-green-50 border-green-300 text-green-700',
    // DFHNEUTR — neutral prompts: 'Press PF5 key to save...', 'Press PF5 key to delete...'
    info: 'bg-gray-50 border-gray-300 text-gray-700',
  };

  return (
    <div
      className={`w-full border rounded px-4 py-2 text-sm font-medium ${variantClasses[variant]} ${className}`}
      role="alert"
    >
      {message}
    </div>
  );
}
