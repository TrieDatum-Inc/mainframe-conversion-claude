/**
 * Cards list page — derived from COCRDLIC (CICS transaction CC0L).
 * BMS map: COCRDLI
 *
 * Supports:
 *   - Optional account_id filter (CARDAIX alt-index browse)
 *   - Keyset pagination (PF7/PF8 → prev/next)
 *   - 10 cards per page (COCRDLIC shows 10 rows)
 */
'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Pagination } from '@/components/ui/Pagination';
import { cardService } from '@/services/cardService';
import { usePagination } from '@/hooks/usePagination';
import { formatCardNumber, formatDate } from '@/lib/utils/format';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { CardListResponse } from '@/lib/types/api';

export default function CardsPage() {
  const searchParams = useSearchParams();
  const accountId = searchParams.get('account_id')
    ? parseInt(searchParams.get('account_id')!, 10)
    : undefined;

  const { cursor, direction, page, goNext, goPrev, reset } = usePagination();
  const [data, setData] = useState<CardListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCards = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await cardService.listCards({
        account_id: accountId,
        cursor,
        limit: 10,
        direction,
      });
      setData(result);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, [accountId, cursor, direction]);

  useEffect(() => {
    reset();
  }, [accountId, reset]);

  useEffect(() => {
    fetchCards();
  }, [fetchCards]);

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Credit Cards</h1>
            <p className="page-subtitle">
              {accountId ? `Cards for Account #${accountId}` : 'All Cards'} — COCRDLIC
            </p>
          </div>
          {accountId && (
            <Link href={ROUTES.ACCOUNT_VIEW(accountId)}>
              <Button variant="outline" size="sm">Back to Account</Button>
            </Link>
          )}
        </div>

        {error && <Alert variant="error" className="mb-4">{error}</Alert>}

        <div className="card">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin h-6 w-6 rounded-full border-4 border-blue-600 border-t-transparent" />
            </div>
          ) : data?.items.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No cards found.</p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Card Number</th>
                      <th>Account ID</th>
                      <th>Embossed Name</th>
                      <th>Expiry</th>
                      <th>Status</th>
                      <th className="sr-only">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data?.items.map((card) => (
                      <tr key={card.card_num} className="hover:bg-gray-50">
                        <td className="font-mono text-sm">{formatCardNumber(card.card_num)}</td>
                        <td>
                          {card.acct_id ? (
                            <Link
                              href={ROUTES.ACCOUNT_VIEW(card.acct_id)}
                              className="text-blue-600 hover:underline"
                            >
                              {card.acct_id}
                            </Link>
                          ) : (
                            '—'
                          )}
                        </td>
                        <td>{card.embossed_name ?? '—'}</td>
                        <td>{formatDate(card.expiration_date)}</td>
                        <td><StatusBadge status={card.active_status} /></td>
                        <td className="text-right">
                          <Link href={ROUTES.CARD_VIEW(card.card_num)}>
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
