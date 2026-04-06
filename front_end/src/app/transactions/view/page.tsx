/**
 * Transaction View page — COTRN01 (BMS map CTRN1A)
 *
 * Route: /transactions/view
 * API: GET /api/v1/transactions/{transaction_id}
 * COBOL program: COTRN01C
 *
 * COTRN01C behavior replicated:
 *   - TRNIDINI input → READ TRANSACT by transaction_id
 *   - All TRAN-RECORD fields displayed (POPULATE-TRAN-FIELDS)
 *   - Error: RESP=NOTFND → 'Transaction ID NOT found on the file'
 *   - Error: TRNIDINI=SPACES → 'Please enter a transaction ID'
 *
 * Bug fix documented:
 *   COTRN01C used READ UPDATE (exclusive lock) for display-only — causes unnecessary
 *   contention. Modern GET uses plain SELECT (no FOR UPDATE clause).
 *
 * Modern additions:
 *   - Query string ?id= supports direct link from list page
 *   - Amount color-coded (negative=debit, positive=credit)
 */

'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Suspense } from 'react';
import { getTransaction, extractError } from '@/lib/api';
import type { TransactionDetailResponse } from '@/types';
import { formatCurrency } from '@/components/ui/CurrencyDisplay';

function TransactionViewContent() {
  const searchParams = useSearchParams();
  const urlId = searchParams.get('id') || '';

  const [transactionId, setTransactionId] = useState(urlId);
  const [transaction, setTransaction] = useState<TransactionDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Auto-load if id passed via query string (link from list page)
  useEffect(() => {
    if (urlId.trim()) {
      loadTransaction(urlId.trim());
    }
  }, [urlId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function loadTransaction(id: string) {
    if (!id.trim()) {
      setError('Please enter a transaction ID');
      return;
    }

    setLoading(true);
    setError('');
    setTransaction(null);

    try {
      const data = await getTransaction(id.trim());
      setTransaction(data);
    } catch (err) {
      const apiErr = extractError(err);
      if (apiErr.error_code === 'TRANSACTION_NOT_FOUND') {
        setError('Transaction ID NOT found on the file');
      } else {
        setError(apiErr.message);
      }
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    loadTransaction(transactionId);
  }

  const amount = transaction ? parseFloat(transaction.amount) : 0;
  const isNeg = !isNaN(amount) && amount < 0;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Transaction View</h1>
          <p className="text-sm text-gray-500 mt-1">
            COTRN01C — view transaction detail by ID
          </p>
        </div>

        {/* Search form — TRNIDINI input field */}
        <form
          onSubmit={handleSearch}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6"
        >
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label
                htmlFor="transactionId"
                className="block text-xs font-medium text-gray-600 mb-1"
              >
                Transaction ID
                <span className="ml-1 text-gray-400">(TRNIDINI — 16 chars)</span>
              </label>
              <input
                id="transactionId"
                type="text"
                value={transactionId}
                onChange={(e) => setTransactionId(e.target.value)}
                maxLength={16}
                placeholder="0000000000000001"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
                autoFocus
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'View'}
            </button>
          </div>
        </form>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Transaction detail card */}
        {transaction && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            {/* Title bar with amount */}
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <div>
                <p className="text-xs text-gray-400 font-mono">Transaction ID</p>
                <p className="text-lg font-mono font-bold text-gray-900">
                  {transaction.transaction_id}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400">Amount</p>
                <p
                  className={`text-2xl font-bold font-mono ${
                    isNeg ? 'text-red-600' : 'text-green-700'
                  }`}
                >
                  {formatCurrency(transaction.amount)}
                </p>
              </div>
            </div>

            {/* Detail fields — maps CTRN1A display fields */}
            <div className="p-6 grid grid-cols-2 gap-x-8 gap-y-4">
              <DetailField
                label="Card Number"
                value={`****${transaction.card_number.slice(-4)}`}
                mono
              />
              <DetailField
                label="Type Code"
                value={transaction.transaction_type_code}
                mono
              />
              <DetailField
                label="Category Code"
                value={transaction.transaction_category_code}
                mono
              />
              <DetailField label="Source" value={transaction.transaction_source} />
              <DetailField label="Description" value={transaction.description} wide />
              <DetailField label="Original Date" value={transaction.original_date} />
              <DetailField label="Processed Date" value={transaction.processed_date} />
              <DetailField label="Merchant ID" value={transaction.merchant_id} mono />
              <DetailField label="Merchant Name" value={transaction.merchant_name} />
              <DetailField label="Merchant City" value={transaction.merchant_city} />
              <DetailField label="Merchant ZIP" value={transaction.merchant_zip} mono />
            </div>

            {/* Actions */}
            <div className="px-6 py-4 border-t border-gray-100 flex gap-3">
              <Link
                href="/transactions/list"
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-300"
              >
                Back to List
              </Link>
            </div>
          </div>
        )}

        {/* Quick nav */}
        <div className="mt-8 pt-4 border-t border-gray-200 flex gap-4 text-sm">
          <Link href="/" className="text-blue-600 hover:underline">
            Main Menu
          </Link>
          <Link href="/transactions/list" className="text-blue-600 hover:underline">
            Transaction List
          </Link>
          <Link href="/transactions/add" className="text-blue-600 hover:underline">
            Add Transaction
          </Link>
        </div>
      </div>
    </div>
  );
}

function DetailField({
  label,
  value,
  mono = false,
  wide = false,
}: {
  label: string;
  value: string | null | undefined;
  mono?: boolean;
  wide?: boolean;
}) {
  return (
    <div className={wide ? 'col-span-2' : ''}>
      <p className="text-xs font-medium text-gray-500">{label}</p>
      <p
        className={`mt-0.5 text-sm text-gray-900 ${mono ? 'font-mono' : ''} ${
          !value ? 'text-gray-400 italic' : ''
        }`}
      >
        {value || 'N/A'}
      </p>
    </div>
  );
}

export default function TransactionViewPage() {
  return (
    <Suspense fallback={<div className="p-6">Loading...</div>}>
      <TransactionViewContent />
    </Suspense>
  );
}
