'use client';

/**
 * Transaction Type List Page
 *
 * COBOL origin: COTRTLIC (Transaction: CTLI) / BMS map CTRTLIA.
 *
 * Maps the CTRTLIA screen to a modern admin data table:
 *   - 7 rows per page (WS-MAX-SCREEN-LINES=7) with standard pagination
 *   - Type code + description filters (TRTYPE/TRDESC fields)
 *   - Edit/Delete buttons per row (replaces 'U'/'D' inline select column)
 *   - "Add New" button (replaces PF2=Add)
 *   - Delete requires modal confirmation (replaces 'D' + ENTER + PF10 two-step)
 *
 * Admin-only: only user_type='A' can access this page.
 * Route protection is enforced by src/middleware.ts.
 */

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  deleteTransactionType,
  extractError,
  listTransactionTypes,
} from '@/lib/api';
import type { TransactionTypeListParams, TransactionTypeResponse } from '@/types';

// ---------------------------------------------------------------------------
// Inline ConfirmDialog component (replaces COTRTLIC 'D' + ENTER + PF10 flow)
// ---------------------------------------------------------------------------

interface ConfirmDialogProps {
  typeCode: string;
  description: string;
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting: boolean;
}

function ConfirmDialog({
  typeCode,
  description,
  onConfirm,
  onCancel,
  isDeleting,
}: ConfirmDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Confirm Delete
        </h2>
        <p className="text-gray-600 mb-1">
          Delete transaction type <span className="font-mono font-bold">{typeCode}</span>?
        </p>
        <p className="text-gray-500 text-sm mb-6">
          Description: {description}
        </p>
        <p className="text-amber-700 text-sm bg-amber-50 border border-amber-200 rounded p-3 mb-6">
          This action cannot be undone. If transactions reference this type code, the
          delete will be rejected.
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            disabled={isDeleting}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
          >
            Cancel (F12)
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="px-4 py-2 text-white bg-red-600 rounded hover:bg-red-700 disabled:opacity-50"
          >
            {isDeleting ? 'Deleting...' : 'Confirm Delete (F10)'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function TransactionTypeListPage() {
  const router = useRouter();

  // List data state
  const [items, setItems] = useState<TransactionTypeResponse[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Pagination state (replaces COTRTLIC WS-CA-SCREEN-NUM + paging keys)
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 7; // WS-MAX-SCREEN-LINES = 7

  // Filter state (replaces COTRTLIC WS-TYPE-CD-FILTER + WS-TYPE-DESC-FILTER)
  const [typeCodeFilter, setTypeCodeFilter] = useState('');
  const [descriptionFilter, setDescriptionFilter] = useState('');
  const [appliedFilters, setAppliedFilters] = useState<TransactionTypeListParams>({});

  // Message state (replaces COTRTLIC INFOMSG + ERRMSG)
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = useState<TransactionTypeResponse | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // ---------------------------------------------------------------------------
  // Data fetching — maps COTRTLIC 8000-READ-FORWARD / 9100-CHECK-FILTERS
  // ---------------------------------------------------------------------------

  const fetchPage = useCallback(
    async (targetPage: number, filters: TransactionTypeListParams) => {
      setIsLoading(true);
      setErrorMessage('');

      try {
        const result = await listTransactionTypes({
          page: targetPage,
          page_size: PAGE_SIZE,
          ...filters,
        });

        setItems(result.items);
        setTotalCount(result.total_count);
        setHasNext(result.has_next);
        setHasPrevious(result.has_previous);

        if (result.items.length === 0) {
          // COTRTLIC: 'No Records found for these filter conditions'
          setErrorMessage('No records found for the current filter conditions.');
        }
      } catch (err) {
        const apiErr = extractError(err);
        setErrorMessage(apiErr.message);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    fetchPage(page, appliedFilters);
  }, [page, appliedFilters, fetchPage]);

  // ---------------------------------------------------------------------------
  // Filter application — maps COTRTLIC 1290-CROSS-EDITS (filter resets paging)
  // ---------------------------------------------------------------------------

  const handleApplyFilters = () => {
    const filters: TransactionTypeListParams = {};
    if (typeCodeFilter.trim()) {
      filters.type_code_filter = typeCodeFilter.trim();
    }
    if (descriptionFilter.trim()) {
      filters.description_filter = descriptionFilter.trim();
    }
    // COTRTLIC: changing filters resets paging to first page
    setPage(1);
    setAppliedFilters(filters);
  };

  const handleClearFilters = () => {
    setTypeCodeFilter('');
    setDescriptionFilter('');
    setPage(1);
    setAppliedFilters({});
  };

  // ---------------------------------------------------------------------------
  // Pagination — replaces COTRTLIC PF7 (backward) / PF8 (forward) cursor paging
  // ---------------------------------------------------------------------------

  const handleNextPage = () => {
    if (hasNext) {
      setPage((p) => p + 1);
      setSuccessMessage('');
    } else {
      setErrorMessage('No more pages to display.');
    }
  };

  const handlePrevPage = () => {
    if (hasPrevious) {
      setPage((p) => p - 1);
      setSuccessMessage('');
    } else {
      setErrorMessage('No previous pages to display.');
    }
  };

  // ---------------------------------------------------------------------------
  // Delete flow — replaces COTRTLIC 'D' + ENTER (highlight) + PF10 (confirm)
  // ---------------------------------------------------------------------------

  const handleDeleteClick = (item: TransactionTypeResponse) => {
    setDeleteTarget(item);
    setErrorMessage('');
    setSuccessMessage('');
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;

    setIsDeleting(true);
    setErrorMessage('');

    try {
      await deleteTransactionType(deleteTarget.type_code);
      setSuccessMessage(
        `Transaction type '${deleteTarget.type_code}' deleted successfully.`
      );
      setDeleteTarget(null);
      // Refresh the current page
      await fetchPage(page, appliedFilters);
    } catch (err) {
      const apiErr = extractError(err);
      // COTRTLIC SQLCODE -532: 'Please delete associated child records first'
      setErrorMessage(apiErr.message);
      setDeleteTarget(null);
    } finally {
      setIsDeleting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header — maps CTRTLIA rows 1-2 (Tran: CTLI / Prog: COTRTLIC) */}
      <div className="bg-blue-900 text-white px-6 py-3">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <span className="text-blue-300 text-sm">Tran: CTLI</span>
            <span className="ml-4 text-blue-300 text-sm">Prog: COTRTLIC</span>
          </div>
          <h1 className="text-yellow-300 font-semibold">
            AWS Mainframe Cloud Demo — Credit Card Demo Application
          </h1>
          <div className="text-blue-300 text-sm">
            {new Date().toLocaleDateString()}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Page title — maps CTRTLIA row 4 'Maintain Transaction Type' */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-800">
            Maintain Transaction Type
          </h2>
          <span className="text-gray-500 text-sm">
            Page {page} of {Math.max(1, Math.ceil(totalCount / PAGE_SIZE))}
            {totalCount > 0 && ` (${totalCount} total)`}
          </span>
        </div>

        {/* Filters — maps CTRTLIA rows 6 and 8 (TRTYPE + TRDESC filter fields) */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div>
              <label className="block text-sm font-medium text-cyan-700 mb-1">
                Type Filter:
              </label>
              {/* TRTYPE field: FSET, UNPROT, GREEN, UNDERLINE */}
              <input
                type="text"
                value={typeCodeFilter}
                onChange={(e) => setTypeCodeFilter(e.target.value)}
                maxLength={2}
                pattern="[0-9]{0,2}"
                placeholder="01-99"
                className="w-full px-3 py-2 border border-gray-300 rounded text-green-700 underline focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-cyan-700 mb-1">
                Description Filter:
              </label>
              {/* TRDESC field: FSET, UNPROT, GREEN, UNDERLINE */}
              <input
                type="text"
                value={descriptionFilter}
                onChange={(e) => setDescriptionFilter(e.target.value)}
                maxLength={50}
                placeholder="Substring search..."
                className="w-full px-3 py-2 border border-gray-300 rounded text-green-700 underline focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleApplyFilters}
                className="flex-1 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
              >
                Apply Filters
              </button>
              <button
                onClick={handleClearFilters}
                className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        {/* Success/Error messages — maps CTRTLIA INFOMSG (row 21) + ERRMSG (row 23) */}
        {successMessage && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded text-center">
            {successMessage}
          </div>
        )}
        {errorMessage && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 rounded font-medium">
            {errorMessage}
          </div>
        )}

        {/* Data table — maps CTRTLIA rows 10-18 (column headers + 7 data rows) */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mb-4">
          {/* Table header — maps CTRTLIA row 10: 'Select Type Description' */}
          <div className="grid grid-cols-12 gap-0 bg-gray-100 border-b border-gray-200 px-4 py-2">
            <div className="col-span-2 text-xs font-semibold text-gray-600 uppercase tracking-wide">
              Type Code
            </div>
            <div className="col-span-7 text-xs font-semibold text-gray-600 uppercase tracking-wide">
              Description
            </div>
            <div className="col-span-3 text-xs font-semibold text-gray-600 uppercase tracking-wide text-right">
              Actions
            </div>
          </div>

          {isLoading ? (
            <div className="px-4 py-8 text-center text-gray-500">
              Loading...
            </div>
          ) : items.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-400">
              No transaction types found.
            </div>
          ) : (
            items.map((item) => (
              <div
                key={item.type_code}
                className="grid grid-cols-12 gap-0 px-4 py-3 border-b border-gray-100 hover:bg-gray-50"
              >
                {/* Type code — maps TRTTYP1-7 (always protected/ASKIP) */}
                <div className="col-span-2 font-mono text-gray-800 font-semibold self-center">
                  {item.type_code}
                </div>
                {/* Description — maps TRTYPD1-7 */}
                <div className="col-span-7 text-gray-700 self-center">
                  {item.description}
                </div>
                {/* Actions — replaces TRTSEL1-7 'U'/'D' select column */}
                <div className="col-span-3 flex gap-2 justify-end self-center">
                  <Link
                    href={`/admin/transaction-types/edit?code=${encodeURIComponent(item.type_code)}`}
                    className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded hover:bg-blue-100 border border-blue-200"
                  >
                    Edit (U)
                  </Link>
                  <button
                    onClick={() => handleDeleteClick(item)}
                    className="px-3 py-1 text-sm bg-red-50 text-red-700 rounded hover:bg-red-100 border border-red-200"
                  >
                    Delete (D)
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Action bar — maps CTRTLIA row 24 function key labels */}
        <div className="flex items-center justify-between">
          <div className="flex gap-3">
            {/* F2=Add — COTRTUPC link */}
            <Link
              href="/admin/transaction-types/add"
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm font-medium"
            >
              F2=Add New
            </Link>
            {/* F3=Exit — return to admin menu */}
            <Link
              href="/admin/menu"
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm"
            >
              F3=Exit
            </Link>
          </div>

          {/* F7/F8 pagination — replaces PF7 (page up) / PF8 (page down) */}
          <div className="flex gap-2 items-center">
            <button
              onClick={handlePrevPage}
              disabled={!hasPrevious || isLoading}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-40 disabled:cursor-not-allowed text-sm"
            >
              F7=Page Up
            </button>
            <span className="text-gray-500 text-sm px-2">
              {page} / {Math.max(1, Math.ceil(totalCount / PAGE_SIZE))}
            </span>
            <button
              onClick={handleNextPage}
              disabled={!hasNext || isLoading}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-40 disabled:cursor-not-allowed text-sm"
            >
              F8=Page Dn
            </button>
          </div>
        </div>
      </div>

      {/* Delete confirmation modal — replaces COTRTLIC 'D' + PF10 two-step */}
      {deleteTarget && (
        <ConfirmDialog
          typeCode={deleteTarget.type_code}
          description={deleteTarget.description}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setDeleteTarget(null)}
          isDeleting={isDeleting}
        />
      )}
    </div>
  );
}
