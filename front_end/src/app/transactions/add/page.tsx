/**
 * Transaction Add page — COTRN02 (BMS map CTRN2A)
 *
 * Route: /transactions/add
 * API: POST /api/v1/transactions
 * COBOL program: COTRN02C
 *
 * COTRN02C behavior replicated:
 *   - VALIDATE-INPUT-FIELDS:
 *       CARDINPI or ACCTIDOI required (mutual exclusion)
 *       TRNAMI != 0 (non-zero amount)
 *       TRNPROCI >= TRNORIGI (processed date must not be before original)
 *       CONFIRMI = 'Y' required
 *   - LOOKUP-ACCT-FROM-CARD: if card_number provided → resolves account_id
 *   - ADD-TRANSACTION: WRITE to TRANSACT VSAM
 *
 * Bug fix documented:
 *   COTRN02C generated transaction_id via STARTBR(HIGH-VALUES)+READPREV+ADD-1.
 *   This had a race condition — two concurrent requests could get the same ID.
 *   Modern API uses PostgreSQL NEXTVAL('transaction_id_seq') — atomic.
 *
 * PF5 equivalent:
 *   "Copy Last Transaction" button — pre-fills form from GET /transactions/last
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { createTransaction, getLastTransaction, extractError } from '@/lib/api';
import type { TransactionDetailResponse } from '@/types';

// ---------------------------------------------------------------------------
// Zod schema — mirrors COTRN02C VALIDATE-INPUT-FIELDS
// ---------------------------------------------------------------------------

const transactionAddSchema = z
  .object({
    card_number: z.string().max(16).optional().or(z.literal('')),
    account_id: z.string().max(11).optional().or(z.literal('')),
    transaction_type_code: z
      .string()
      .min(1, 'Transaction type code is required')
      .max(2),
    transaction_category_code: z.string().max(4).optional().or(z.literal('')),
    transaction_source: z.string().max(10).optional().or(z.literal('')),
    description: z.string().max(60).optional().or(z.literal('')),
    // TRNAMI != 0
    amount: z
      .string()
      .min(1, 'Amount is required')
      .refine(
        (v) => !isNaN(parseFloat(v)) && parseFloat(v) !== 0,
        'Amount must not be zero'
      ),
    // TRNORIGDT
    original_date: z.string().min(1, 'Original date is required'),
    // TRNPROCDT >= TRNORIGDT
    processed_date: z.string().min(1, 'Processed date is required'),
    merchant_id: z.string().max(9).optional().or(z.literal('')),
    merchant_name: z.string().max(30).optional().or(z.literal('')),
    merchant_city: z.string().max(25).optional().or(z.literal('')),
    merchant_zip: z.string().max(10).optional().or(z.literal('')),
    confirm: z.literal('Y', {
      errorMap: () => ({
        message: "Confirmation required — change to 'Y' to proceed",
      }),
    }),
  })
  // COTRN02C: CARDINPI or ACCTIDOI required (mutual exclusion)
  .refine(
    (d) => (d.card_number && d.card_number.trim()) || (d.account_id && d.account_id.trim()),
    {
      message: 'Either Card Number or Account ID must be provided',
      path: ['card_number'],
    }
  )
  // COTRN02C: TRNPROCI >= TRNORIGI (CSUTLDTC date order check)
  .refine(
    (d) => {
      if (d.original_date && d.processed_date) {
        return d.processed_date >= d.original_date;
      }
      return true;
    },
    {
      message: 'Processed date must not be before original date',
      path: ['processed_date'],
    }
  );

type FormValues = z.infer<typeof transactionAddSchema>;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TransactionAddPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState('');
  const [successTranId, setSuccessTranId] = useState('');
  const [loadingLast, setLoadingLast] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(transactionAddSchema),
    defaultValues: {
      confirm: 'Y',
      original_date: new Date().toISOString().split('T')[0],
      processed_date: new Date().toISOString().split('T')[0],
    },
  });

  // PF5 equivalent: COPY-LAST-TRAN-DATA
  async function copyLastTransaction() {
    setLoadingLast(true);
    try {
      const last: TransactionDetailResponse | null = await getLastTransaction();
      if (!last) {
        setServerError('No previous transaction found to copy.');
        return;
      }
      setValue('card_number', last.card_number || '');
      setValue('transaction_type_code', last.transaction_type_code || '');
      setValue('transaction_category_code', last.transaction_category_code || '');
      setValue('transaction_source', last.transaction_source || '');
      setValue('description', last.description || '');
      setValue('amount', last.amount || '');
      setValue('original_date', last.original_date || '');
      setValue('processed_date', last.processed_date || '');
      setValue('merchant_id', last.merchant_id || '');
      setValue('merchant_name', last.merchant_name || '');
      setValue('merchant_city', last.merchant_city || '');
      setValue('merchant_zip', last.merchant_zip || '');
    } catch {
      setServerError('Failed to load last transaction.');
    } finally {
      setLoadingLast(false);
    }
  }

  async function onSubmit(values: FormValues) {
    setSubmitting(true);
    setServerError('');
    setSuccessTranId('');

    try {
      const payload: Record<string, unknown> = {
        transaction_type_code: values.transaction_type_code,
        amount: values.amount,
        original_date: values.original_date,
        processed_date: values.processed_date,
        confirm: 'Y',
      };

      if (values.card_number?.trim()) payload.card_number = values.card_number.trim();
      if (values.account_id?.trim())
        payload.account_id = parseInt(values.account_id.trim(), 10);
      if (values.transaction_category_code?.trim())
        payload.transaction_category_code = values.transaction_category_code.trim();
      if (values.transaction_source?.trim())
        payload.transaction_source = values.transaction_source.trim();
      if (values.description?.trim()) payload.description = values.description.trim();
      if (values.merchant_id?.trim()) payload.merchant_id = values.merchant_id.trim();
      if (values.merchant_name?.trim()) payload.merchant_name = values.merchant_name.trim();
      if (values.merchant_city?.trim()) payload.merchant_city = values.merchant_city.trim();
      if (values.merchant_zip?.trim()) payload.merchant_zip = values.merchant_zip.trim();

      const result = await createTransaction(payload as Parameters<typeof createTransaction>[0]);
      setSuccessTranId(result.transaction_id);
      reset();
    } catch (err) {
      const apiErr = extractError(err);
      if (apiErr.error_code === 'CARD_NOT_FOUND') {
        setServerError('Card number not found in the system.');
      } else if (apiErr.error_code === 'ACCOUNT_NOT_FOUND') {
        setServerError('Account ID not found in the system.');
      } else if (apiErr.error_code === 'TRANSACTION_TYPE_NOT_FOUND') {
        setServerError('Transaction type code is invalid.');
      } else {
        setServerError(apiErr.message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Add Transaction</h1>
            <p className="text-sm text-gray-500 mt-1">COTRN02C — create a new transaction</p>
          </div>
          <button
            type="button"
            onClick={copyLastTransaction}
            disabled={loadingLast}
            className="px-4 py-2 bg-yellow-100 text-yellow-800 border border-yellow-300 rounded-md text-sm font-medium hover:bg-yellow-200 disabled:opacity-50"
          >
            {loadingLast ? 'Loading...' : 'PF5: Copy Last Transaction'}
          </button>
        </div>

        {/* Success */}
        {successTranId && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm font-medium text-green-800">
              Transaction created successfully.
            </p>
            <p className="text-sm text-green-700 font-mono mt-1">
              Transaction ID: {successTranId}
            </p>
            <div className="mt-2 flex gap-2">
              <Link
                href={`/transactions/view?id=${encodeURIComponent(successTranId)}`}
                className="text-sm text-blue-600 hover:underline"
              >
                View transaction
              </Link>
              <span className="text-gray-400">|</span>
              <Link href="/transactions/list" className="text-sm text-blue-600 hover:underline">
                Back to list
              </Link>
            </div>
          </div>
        )}

        {/* Server error */}
        {serverError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{serverError}</p>
          </div>
        )}

        {/* Form */}
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-5"
        >
          {/* Card / Account section */}
          <fieldset>
            <legend className="text-sm font-semibold text-gray-700 mb-3">
              Card / Account Identification
              <span className="text-xs text-gray-400 font-normal ml-2">
                (COTRN02C: CARDINPI XOR ACCTIDOI)
              </span>
            </legend>
            <div className="grid grid-cols-2 gap-4">
              <FormField
                label="Card Number"
                hint="16-digit card number"
                error={errors.card_number?.message}
              >
                <input
                  {...register('card_number')}
                  type="text"
                  maxLength={16}
                  placeholder="4111111111111001"
                  className={inputClass(!!errors.card_number)}
                />
              </FormField>
              <FormField
                label="Account ID"
                hint="11-digit account; provide card OR account"
                error={errors.account_id?.message}
              >
                <input
                  {...register('account_id')}
                  type="text"
                  maxLength={11}
                  placeholder="10000000001"
                  className={inputClass(!!errors.account_id)}
                />
              </FormField>
            </div>
          </fieldset>

          {/* Transaction details */}
          <fieldset>
            <legend className="text-sm font-semibold text-gray-700 mb-3">
              Transaction Details
            </legend>
            <div className="grid grid-cols-2 gap-4">
              <FormField
                label="Type Code *"
                hint="2-digit type (e.g. 01)"
                error={errors.transaction_type_code?.message}
              >
                <input
                  {...register('transaction_type_code')}
                  type="text"
                  maxLength={2}
                  placeholder="01"
                  className={inputClass(!!errors.transaction_type_code)}
                />
              </FormField>
              <FormField
                label="Category Code"
                hint="4-digit category"
                error={errors.transaction_category_code?.message}
              >
                <input
                  {...register('transaction_category_code')}
                  type="text"
                  maxLength={4}
                  placeholder="1001"
                  className={inputClass(!!errors.transaction_category_code)}
                />
              </FormField>
              <FormField
                label="Source"
                hint="up to 10 chars"
                error={errors.transaction_source?.message}
              >
                <input
                  {...register('transaction_source')}
                  type="text"
                  maxLength={10}
                  placeholder="POS TERM"
                  className={inputClass(!!errors.transaction_source)}
                />
              </FormField>
              <FormField
                label="Amount *"
                hint="Non-zero; negative for debits"
                error={errors.amount?.message}
              >
                <input
                  {...register('amount')}
                  type="text"
                  placeholder="-52.47"
                  className={inputClass(!!errors.amount)}
                />
              </FormField>
              <FormField
                label="Description"
                hint="up to 60 chars"
                error={errors.description?.message}
                wide
              >
                <input
                  {...register('description')}
                  type="text"
                  maxLength={60}
                  className={inputClass(!!errors.description)}
                />
              </FormField>
            </div>
          </fieldset>

          {/* Dates */}
          <fieldset>
            <legend className="text-sm font-semibold text-gray-700 mb-3">
              Dates
              <span className="text-xs text-gray-400 font-normal ml-2">
                (processed &ge; original — CSUTLDTC order check)
              </span>
            </legend>
            <div className="grid grid-cols-2 gap-4">
              <FormField
                label="Original Date *"
                error={errors.original_date?.message}
              >
                <input
                  {...register('original_date')}
                  type="date"
                  className={inputClass(!!errors.original_date)}
                />
              </FormField>
              <FormField
                label="Processed Date *"
                error={errors.processed_date?.message}
              >
                <input
                  {...register('processed_date')}
                  type="date"
                  className={inputClass(!!errors.processed_date)}
                />
              </FormField>
            </div>
          </fieldset>

          {/* Merchant */}
          <fieldset>
            <legend className="text-sm font-semibold text-gray-700 mb-3">Merchant</legend>
            <div className="grid grid-cols-2 gap-4">
              <FormField label="Merchant ID" hint="9-digit" error={errors.merchant_id?.message}>
                <input
                  {...register('merchant_id')}
                  type="text"
                  maxLength={9}
                  placeholder="100000001"
                  className={inputClass(!!errors.merchant_id)}
                />
              </FormField>
              <FormField label="Merchant Name" error={errors.merchant_name?.message}>
                <input
                  {...register('merchant_name')}
                  type="text"
                  maxLength={30}
                  className={inputClass(!!errors.merchant_name)}
                />
              </FormField>
              <FormField label="City" error={errors.merchant_city?.message}>
                <input
                  {...register('merchant_city')}
                  type="text"
                  maxLength={25}
                  className={inputClass(!!errors.merchant_city)}
                />
              </FormField>
              <FormField label="ZIP" error={errors.merchant_zip?.message}>
                <input
                  {...register('merchant_zip')}
                  type="text"
                  maxLength={10}
                  className={inputClass(!!errors.merchant_zip)}
                />
              </FormField>
            </div>
          </fieldset>

          {/* Confirmation — COTRN02C CONFIRMI='Y' gate */}
          <div className="flex items-center gap-3 pt-2 border-t border-gray-100">
            <div>
              <label htmlFor="confirm" className="block text-sm font-medium text-gray-700">
                Confirm (CONFIRMI)
                <span className="text-xs text-gray-400 ml-1">
                  — must be &apos;Y&apos; to submit
                </span>
              </label>
              <select
                {...register('confirm')}
                id="confirm"
                className={`mt-1 px-3 py-2 border rounded-md text-sm ${
                  errors.confirm ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="Y">Y — Yes, add this transaction</option>
                <option value="N">N — No, do not add</option>
              </select>
              {errors.confirm && (
                <p className="text-xs text-red-600 mt-0.5">{errors.confirm.message}</p>
              )}
            </div>

            <div className="ml-auto flex gap-3">
              <Link
                href="/transactions/list"
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-300"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? 'Adding...' : 'Add Transaction'}
              </button>
            </div>
          </div>
        </form>

        {/* Quick nav */}
        <div className="mt-6 pt-4 border-t border-gray-200 flex gap-4 text-sm">
          <Link href="/" className="text-blue-600 hover:underline">
            Main Menu
          </Link>
          <Link href="/transactions/list" className="text-blue-600 hover:underline">
            Transaction List
          </Link>
        </div>
      </div>
    </div>
  );
}

function inputClass(hasError: boolean) {
  return `w-full px-3 py-2 border rounded-md text-sm ${
    hasError ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
  } focus:outline-none focus:ring-1`;
}

function FormField({
  label,
  hint,
  error,
  children,
  wide = false,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
  wide?: boolean;
}) {
  return (
    <div className={wide ? 'col-span-2' : ''}>
      <label className="block text-xs font-medium text-gray-600 mb-1">
        {label}
        {hint && <span className="ml-1 text-gray-400 font-normal">{hint}</span>}
      </label>
      {children}
      {error && <p className="text-xs text-red-600 mt-0.5">{error}</p>}
    </div>
  );
}
