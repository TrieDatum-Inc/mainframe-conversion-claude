'use client';

/**
 * LoadingSpinner — shown during async API calls.
 * Replaces the CICS "X SYSTEM" wait indicator on the mainframe terminal.
 */

export function LoadingSpinner({ label = 'Loading...' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-8" role="status">
      <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-3" />
      <span className="text-gray-600 text-sm">{label}</span>
    </div>
  );
}
