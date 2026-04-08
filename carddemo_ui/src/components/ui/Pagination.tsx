/**
 * Pagination component — maps to COBOL PF7/PF8 key navigation.
 * Used in all list screens (COTRN00, COCRDLI, COUSR00, COTRTLI).
 */
import React from 'react';
import { cn } from '@/lib/utils/cn';

interface PaginationProps {
  page: number;
  hasNext: boolean;
  hasPrev: boolean;
  onNext: () => void;
  onPrev: () => void;
  total?: number;
  limit?: number;
  className?: string;
}

export function Pagination({
  page,
  hasNext,
  hasPrev,
  onNext,
  onPrev,
  total,
  className,
}: PaginationProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between border-t border-gray-200 pt-4',
        className
      )}
    >
      <div className="text-sm text-gray-500">
        {total !== undefined && (
          <span>
            {total} total record{total !== 1 ? 's' : ''}
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-600">Page {page}</span>
        <div className="flex gap-2">
          {/* PF7 — Previous page */}
          <button
            onClick={onPrev}
            disabled={!hasPrev}
            aria-label="Previous page (PF7)"
            className={cn(
              'inline-flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1',
              'transition-colors',
              hasPrev
                ? 'text-gray-700 hover:bg-gray-50 cursor-pointer'
                : 'text-gray-400 cursor-not-allowed bg-gray-50'
            )}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="h-4 w-4"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
            Previous
          </button>

          {/* PF8 — Next page */}
          <button
            onClick={onNext}
            disabled={!hasNext}
            aria-label="Next page (PF8)"
            className={cn(
              'inline-flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1',
              'transition-colors',
              hasNext
                ? 'text-gray-700 hover:bg-gray-50 cursor-pointer'
                : 'text-gray-400 cursor-not-allowed bg-gray-50'
            )}
          >
            Next
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="h-4 w-4"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
