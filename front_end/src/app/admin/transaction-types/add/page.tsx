'use client';

/**
 * Transaction Type Add Page
 *
 * COBOL origin: COTRTUPC (Transaction: CTTU) / BMS map CTRTUPA.
 * State: TTUP-CREATE-NEW-RECORD → PF5 → 9700-INSERT-RECORD.
 *
 * Maps the CTRTUPA detail form to a modern add form:
 *   - Type Code field (TRTYPCD): 2-digit numeric, required, non-zero
 *   - Description field (TRTYDSC): alphanumeric only, max 50 chars
 *   - Save button (replaces PF5=Save)
 *   - Cancel button (replaces F12=Cancel / F3=Exit)
 *
 * Validation matches COTRTUPC 1200-EDIT-MAP-INPUTS:
 *   - 1210-EDIT-TRANTYPE: numeric, non-zero
 *   - 1230-EDIT-ALPHANUM-REQD: alphanumeric only, non-blank
 *
 * Admin-only: route protected by middleware.ts.
 */

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { createTransactionType, extractError } from '@/lib/api';

// ---------------------------------------------------------------------------
// Zod validation schema — mirrors COTRTUPC 1200-EDIT-MAP-INPUTS
// ---------------------------------------------------------------------------

/**
 * Validation schema for the add form.
 * Rules mirror COTRTUPC validation paragraphs exactly.
 */
const addSchema = z.object({
  type_code: z
    .string()
    .min(1, 'Transaction type code is required')
    .max(2, 'Type code must be 1-2 digits')
    .regex(/^[0-9]{1,2}$/, 'Type code must be numeric (01-99)')
    .refine((v) => parseInt(v, 10) > 0, {
      message: 'Transaction type code must not be zero',
      // COTRTUPC 1210-EDIT-TRANTYPE non-zero check
    }),
  description: z
    .string()
    .min(1, 'Description is required')
    .max(50, 'Description must not exceed 50 characters')
    .regex(/^[A-Za-z0-9 ]+$/, 'Description must contain only letters, numbers, and spaces')
    // COTRTUPC 1230-EDIT-ALPHANUM-REQD
    .refine((v) => v.trim().length > 0, { message: 'Description cannot be blank' }),
});

type AddFormValues = z.infer<typeof addSchema>;

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function TransactionTypeAddPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<AddFormValues>({
    resolver: zodResolver(addSchema),
    defaultValues: { type_code: '', description: '' },
  });

  // ---------------------------------------------------------------------------
  // Submit handler — maps COTRTUPC 9700-INSERT-RECORD + EXEC CICS SYNCPOINT
  // ---------------------------------------------------------------------------

  const onSubmit = async (data: AddFormValues) => {
    setIsSubmitting(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const created = await createTransactionType({
        type_code: data.type_code,
        description: data.description,
      });

      // COTRTUPC TTUP-CHANGES-OKAYED-AND-DONE
      setSuccessMessage(
        `Transaction type '${created.type_code}' created successfully.`
      );
      reset();

      // Navigate back to list after short delay
      setTimeout(() => router.push('/admin/transaction-types'), 1500);
    } catch (err) {
      const apiErr = extractError(err);
      // Map error codes to user-friendly messages
      if (apiErr.error_code === 'TRANSACTION_TYPE_ALREADY_EXISTS') {
        setErrorMessage(`Transaction type '${data.type_code}' already exists.`);
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
        {/* Page title — maps CTRTUPA row 7 'Maintain Transaction Type' */}
        <h2 className="text-xl font-semibold text-gray-800 mb-6">
          Add Transaction Type
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

        {/* Form — maps CTRTUPA rows 12 (TRTYPCD) and 14 (TRTYDSC) */}
        <form onSubmit={handleSubmit(onSubmit)} className="bg-white rounded-lg border border-gray-200 p-6">
          {/* Transaction Type Code — maps CTRTUPA TRTYPCD field */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-cyan-700 mb-1">
              Transaction Type:{' '}
              <span className="text-red-500">*</span>
            </label>
            {/*
              COTRTUPC: TRTYPCD — DFHBMFSE UNPROT NUM, 2 chars.
              Accepts numeric 01-99 only (COTRTUPC 1210-EDIT-TRANTYPE).
            */}
            <input
              {...register('type_code')}
              type="text"
              maxLength={2}
              inputMode="numeric"
              placeholder="01"
              autoFocus
              className={`w-24 px-3 py-2 border rounded font-mono text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.type_code ? 'border-red-400 bg-red-50' : 'border-gray-300'
              }`}
            />
            {errors.type_code && (
              <p className="mt-1 text-sm text-red-600">{errors.type_code.message}</p>
            )}
            <p className="mt-1 text-xs text-gray-400">
              Enter a 2-digit numeric code (01-99).
            </p>
          </div>

          {/* Description — maps CTRTUPA TRTYDSC field */}
          <div className="mb-8">
            <label className="block text-sm font-medium text-cyan-700 mb-1">
              Description:{' '}
              <span className="text-red-500">*</span>
            </label>
            {/*
              COTRTUPC: TRTYDSC — DFHBMFSE UNPROT, 50 chars.
              Alphanumeric only (COTRTUPC 1230-EDIT-ALPHANUM-REQD).
            */}
            <input
              {...register('description')}
              type="text"
              maxLength={50}
              placeholder="Enter description (letters, numbers, spaces only)"
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

          {/* Action bar — maps CTRTUPA row 24: ENTER=Process F3=Exit F5=Save F12=Cancel */}
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
      </div>
    </div>
  );
}
