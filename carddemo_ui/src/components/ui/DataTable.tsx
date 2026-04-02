'use client';

// ============================================================
// DataTable — Sortable table with pagination controls
// Supports cursor-based pagination (has_next_page) from backend
// ============================================================

import { ChevronLeft, ChevronRight } from 'lucide-react';

export interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string | number;
  currentPage: number;
  pageSize: number;
  hasNextPage?: boolean;
  onPageChange: (page: number) => void;
  onRowClick?: (row: T) => void;
  isLoading?: boolean;
  emptyMessage?: string;
}

function getCellValue<T>(row: T, key: keyof T | string): React.ReactNode {
  const val = (row as Record<string, unknown>)[key as string];
  if (val === null || val === undefined) return '—';
  return String(val);
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  currentPage,
  pageSize,
  hasNextPage = false,
  onPageChange,
  onRowClick,
  isLoading = false,
  emptyMessage = 'No records found',
}: DataTableProps<T>) {
  const hasPrev = currentPage > 1;
  const hasNext = hasNextPage;

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              {columns.map((col) => (
                <th
                  key={String(col.key)}
                  className={`px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider ${col.className ?? ''}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading
              ? Array.from({ length: pageSize }).map((_, i) => (
                  <tr key={i} className="border-b border-slate-100">
                    {columns.map((col) => (
                      <td key={String(col.key)} className="px-4 py-3">
                        <div className="h-4 rounded bg-slate-100 animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              : data.length === 0
              ? (
                  <tr>
                    <td
                      colSpan={columns.length}
                      className="px-4 py-12 text-center text-sm text-slate-400"
                    >
                      {emptyMessage}
                    </td>
                  </tr>
                )
              : data.map((row) => (
                  <tr
                    key={keyExtractor(row)}
                    onClick={() => onRowClick?.(row)}
                    className={`border-b border-slate-100 last:border-0 transition-colors ${
                      onRowClick
                        ? 'cursor-pointer hover:bg-blue-50'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    {columns.map((col) => (
                      <td
                        key={String(col.key)}
                        className={`px-4 py-3 text-slate-700 ${col.className ?? ''}`}
                      >
                        {col.render
                          ? col.render(row)
                          : getCellValue(row, col.key)}
                      </td>
                    ))}
                  </tr>
                ))}
          </tbody>
        </table>
      </div>

      {/* Pagination controls — maps to PF7/PF8 (Page Up/Down) */}
      {(data.length > 0 || currentPage > 1) && (
        <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-4 py-3">
          <p className="text-xs text-slate-500">
            Showing {data.length} records (page {currentPage})
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={!hasPrev}
              className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              aria-label="Previous page (PF7)"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              Prev
            </button>

            <span className="px-3 py-1.5 text-xs font-medium text-slate-700">
              Page {currentPage}
            </span>

            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={!hasNext}
              className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              aria-label="Next page (PF8)"
            >
              Next
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
