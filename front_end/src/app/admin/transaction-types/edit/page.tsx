'use client';

/**
 * Transaction Type Edit Page
 *
 * COBOL origin: COTRTUPC (Transaction: CTTU) / BMS map CTRTUPA.
 * State: TTUP-SHOW-DETAILS → user edits → ENTER → TTUP-CHANGES-OK-NOT-CONFIRMED → PF5
 *
 * Maps the CTRTUPA detail form (edit mode) to a modern update form:
 *   - Type Code: read-only (disabled) — always protected on both COTRTLIC and COTRTUPC
 *   - Description: editable input field
 *   - Save button (PF5=Save) with optimistic locking (replaces WS-DATACHANGED-FLAG)
 *   - Cancel button (F12=Cancel)
 *
 * Optimistic locking:
 *   The page fetches the record including updated_at, passes it on PUT.
 *   If another user modified the record, the server returns 409 Conflict
 *   (replaces COTRTLIC WS-DATACHANGED-FLAG / COTRTUPC 1205-COMPARE-OLD-NEW).
 *
 * Query param: ?code=XX (the type_code to edit)
 * Admin-only: route protected by middleware.ts.
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { extractError, getTransactionType, updateTransactionType } from '@/lib/api';
import type { TransactionTypeResponse } from '@/types';

// ---------------------------------------------------------------------------
// Zod validation schema — mirrors COTRTUPC update validation
// ---------------------------------------------------------------------------

const editSchema = z.object({
  description: z
    .string()
    .min(1, 'Description is required')
    .max(50, 'Description must not exceed 50 characters')
    .regex(/^[A-Za-z0-9 ]+$/, 'Description must contain only letters, numbers, and spaces')
    // COTRTUPC 1230-EDIT-ALPHANUM-REQD
    .refine((v) => v.trim().length > 0, { message: 'Description cannot be blank' }),
});

type EditFormValues = z.infer<typeof editSchema>;

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function TransactionTypeEditPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const typeCode = searchParams.get('code') || '';

  const [currentRecord, setCurrentRecord] = useState<TransactionTypeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
  });

  // ---------------------------------------------------------------------------
  // Fetch existing record — maps COTRTUPC 9000-READ-TRANTYPE → 9100-GET-TRANSACTION-TYPE
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (!typeCode) {
      setErrorMessage('No type code provided. Please select a record from the list.');
      setIsLoading(false);
      return;
    }

    const fetchRecord = async () => {
      setIsLoading(true);
      setErrorMessage('');

      try {
        const record = await getTransactionType(typeCode);
        setCurrentRecord(record);
        reset({ description: record.description });
      } catch (err) {
        const apiErr = extractError(err);
        if (apiErr.error_code === 'TRANSACTION_TYPE_NOT_FOUND') {
          // COTRTUPC TTUP-DETAILS-NOT-FOUND
          setErrorMessage(`Transaction type '${typeCode}' not found. It may have been deleted.`);
        } else {
          setErrorMessage(apiErr.message);
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecord();
  }, [typeCode, reset]);

  // ---------------------------------------------------------------------------
  // Submit handler — maps COTRTUPC 9600-WRITE-PROCESSING (UPDATE path)
  // ---------------------------------------------------------------------------

  const onSubmit = async (data: EditFormValues) => {
    if (!currentRecord) return;

    setIsSubmitting(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const updated = await updateTransactionType(typeCode, {
        description: data.description,
        // Pass the updated_at as the optimistic lock version
        // Replaces COTRTLIC WS-DATACHANGED-FLAG / COTRTUPC 1205-COMPARE-OLD-NEW
        optimistic_lock_version: currentRecord.updated_at,
      });

      // COTRTUPC TTUP-CHANGES-OKAYED-AND-DONE
      setSuccessMessage(`Transaction type '${updated.type_code}' updated successfully.`);
      setCurrentRecord(updated);
      reset({ description: updated.description });

      setTimeout(() => router.push('/admin/transaction-types'), 1500);
    } catch (err) {
      const apiErr = extractError(err);

      if (apiErr.error_code === 'NO_CHANGES_DETECTED') {
        // COTRTLIC WS-MESG-NO-CHANGES-DETECTED
        setErrorMessage('No change detected with respect to database values.');
      } else if (apiErr.error_code === 'OPTIMISTIC_LOCK_CONFLICT') {
        // COTRTLIC WS-DATACHANGED-FLAG: another user changed this record
        setErrorMessage(
          `This record was modified by another user. Please refresh to see the latest version.`
        );
        // Reload to get fresh data
        try {
          const refreshed = await getTransactionType(typeCode);
          setCurrentRecord(refreshed);
          reset({ description: refreshed.description });
        } catch {
          // If refresh fails too, let the user navigate back
        }
      } else if (apiErr.error_code === 'TRANSACTION_TYPE_NOT_FOUND') {
        // COTRTLIC 9200-UPDATE-RECORD SQLCODE +100: 'Record not found. Deleted by others?'
        setErrorMessage(`Transaction type '${typeCode}' not found. It may have been deleted.`);
      } else {
        setErrorMessage(apiErr.message);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header — maps CTRTUPA rows 1-2 */}
      <div className="bg-blue-900 text-white px-6 py-3">
        <div className="max-w-2xl mx-auto flex justify-between items-center">
          <div>
            <span className="text-blue-300 text-sm">Tran: CTTU</span>
            <span className="ml-4 text-blue-300 text-sm">Prog: COTRTUPC</span>
          </div>
          <h1 className="text-yellow-300 font-semibold">
            AWS Mainframe Cloud Demo
          </h1>
          <div className="text-blue-300 text-sm">
            {new Date().toLocaleDateString()}
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-8">
        {/* Page title — maps CTRTUPA row 7 */}
        <h2 className="text-xl font-semibold text-gray-800 mb-6">
          Edit Transaction Type
        </h2>

        {/* Messages — maps CTRTUPA INFOMSG (row 22) + ERRMSG (row 23) */}
        {successMessage && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded">
            {successMessage}
          </div>
        )}
        {errorMessage && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 rounded font-medium">
            {errorMessage}
          </div>
        )}

        {/* Form — maps CTRTUPA rows 12 (TRTYPCD read-only) and 14 (TRTYDSC editable) */}
        {currentRecord ? (
          <form onSubmit={handleSubmit(onSubmit)} className="bg-white rounded-lg border border-gray-200 p-6">
            {/* Type Code — read-only (always ASKIP/PROT on CTRTUPA edit path) */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-cyan-700 mb-1">
                Transaction Type:
              </label>
              {/*
                COTRTUPC: On edit, TRTYPCD is DFHBMPRF (protected/ASKIP).
                Type code can never be changed — only description is editable.
              */}
              <div className="w-24 px-3 py-2 bg-gray-100 border border-gray-200 rounded font-mono text-gray-600">
                {currentRecord.type_code}
              </div>
              <p className="mt-1 text-xs text-gray-400">
                Type code cannot be changed.
              </p>
            </div>

            {/* Description — editable (DFHBMFSE UNPROT on update path) */}
            <div className="mb-8">
              <label className="block text-sm font-medium text-cyan-700 mb-1">
                Description:{' '}
                <span className="text-red-500">*</span>
              </label>
              <input
                {...register('description')}
                type="text"
                maxLength={50}
                placeholder="Enter description"
                autoFocus
                className={`w-full px-3 py-2 border rounded text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.description ? 'border-red-400 bg-red-50' : 'border-gray-300'
                }`}
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
              )}
              <p className="mt-1 text-xs text-gray-400">
                Max 50 characters. Letters, numbers, and spaces only.
              </p>
            </div>

            {/* Metadata — shows optimistic lock timestamp for debugging */}
            <div className="mb-6 text-xs text-gray-400">
              Last updated: {new Date(currentRecord.updated_at).toLocaleString()}
            </div>

            {/* Action bar — maps CTRTUPA row 24 */}
            <div className="flex gap-3 justify-between">
              <div className="flex gap-3">
                {/* F5=Save — COTRTUPC PF5 → 9600-WRITE-PROCESSING */}
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 font-medium"
                >
                  {isSubmitting ? 'Saving...' : 'F5=Save'}
                </button>
                {/* F12=Cancel — COTRTUPC TTUP-CHANGES-BACKED-OUT */}
                <Link
                  href="/admin/transaction-types"
                  className="px-6 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                >
                  F12=Cancel
                </Link>
              </div>
              {/* F3=Exit — back to admin menu */}
              <Link
                href="/admin/menu"
                className="px-4 py-2 text-gray-500 hover:text-gray-700 text-sm"
              >
                F3=Exit
              </Link>
            </div>
          </form>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <p className="text-gray-500 mb-4">Record not available.</p>
            <Link
              href="/admin/transaction-types"
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Back to List
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
