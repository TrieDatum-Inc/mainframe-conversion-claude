/**
 * Transactions list — derived from COTRN00C (CICS transaction CT00).
 * BMS map: COTRN00
 *
 * Features:
 *   - Optional filter by card_num or account_id
 *   - Keyset pagination (PF7=prev, PF8=next)
 *   - 10 rows per screen (COTRN00C default)
 */
'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { Pagination } from '@/components/ui/Pagination';
import { transactionService } from '@/services/transactionService';
import { usePagination } from '@/hooks/usePagination';
import { formatCurrency, formatTimestamp, truncate } from '@/lib/utils/format';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { TransactionListResponse } from '@/lib/types/api';

export default function TransactionsPage() {
  const searchParams = useSearchParams();
  const cardNum = searchParams.get('card_num') ?? undefined;
  const acctId = searchParams.get('acct_id')
    ? parseInt(searchParams.get('acct_id')!, 10)
    : undefined;

  const { cursor, direction, page, goNext, goPrev, reset } = usePagination();
  const [data, setData] = useState<TransactionListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTransactions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await transactionService.listTransactions({
        cursor,
        direction,
        limit: 10,
        card_num: cardNum,
        acct_id: acctId,
      });
      setData(result);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, [cursor, direction, cardNum, acctId]);

  useEffect(() => {
    reset();
  }, [cardNum, acctId, reset]);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Transactions</h1>
            <p className="page-subtitle">
              {cardNum ? `Card: ${cardNum}` : acctId ? `Account #${acctId}` : 'All Transactions'} — COTRN00C
            </p>
          </div>
          <Link href={ROUTES.TRANSACTION_NEW}>
            <Button variant="primary" size="sm">
              + New Transaction
            </Button>
          </Link>
        </div>

        {error && <Alert variant="error" className="mb-4">{error}</Alert>}

        <div className="card">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin h-6 w-6 rounded-full border-4 border-blue-600 border-t-transparent" />
            </div>
          ) : data?.items.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No transactions found.</p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Transaction ID</th>
                      <th>Type</th>
                      <th>Amount</th>
                      <th>Description</th>
                      <th>Merchant</th>
                      <th>Card</th>
                      <th>Date</th>
                      <th className="sr-only">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data?.items.map((txn) => (
                      <tr key={txn.tran_id} className="hover:bg-gray-50">
                        <td className="font-mono text-xs">{txn.tran_id}</td>
                        <td>
                          <span className="badge text-blue-700 bg-blue-50 ring-blue-600/20">
                            {txn.type_cd ?? '—'}
                          </span>
                        </td>
                        <td className="font-semibold">{formatCurrency(txn.amount)}</td>
                        <td className="text-gray-600">{truncate(txn.description ?? '—', 30)}</td>
                        <td>{txn.merchant_name ? truncate(txn.merchant_name, 20) : '—'}</td>
                        <td className="font-mono text-xs">{txn.card_num ?? '—'}</td>
                        <td className="text-gray-500">{formatTimestamp(txn.orig_ts)}</td>
                        <td>
                          <Link href={ROUTES.TRANSACTION_VIEW(txn.tran_id)}>
                            <Button variant="ghost" size="sm">View</Button>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <Pagination
                page={page}
                hasNext={!!data?.next_cursor}
                hasPrev={!!data?.prev_cursor}
                onNext={() => goNext(data?.next_cursor)}
                onPrev={() => goPrev(data?.prev_cursor)}
                total={data?.total}
              />
            </>
          )}
        </div>
      </div>
    </AppShell>
  );
}
