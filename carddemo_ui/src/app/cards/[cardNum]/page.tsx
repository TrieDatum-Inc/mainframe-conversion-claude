/**
 * Card detail view — derived from COCRDSLC (CICS transaction CC0S).
 * BMS map: COCRDSL
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { cardService } from '@/services/cardService';
import { formatCardNumber, formatDate } from '@/lib/utils/format';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { CardResponse } from '@/lib/types/api';

interface PageProps {
  params: { cardNum: string };
}

export default function CardDetailPage({ params }: PageProps) {
  const { cardNum } = params;
  const [card, setCard] = useState<CardResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    cardService
      .getCard(cardNum)
      .then(setCard)
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [cardNum]);

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin h-8 w-8 rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Card Details</h1>
            <p className="page-subtitle">COCRDSLC</p>
          </div>
          <div className="flex gap-2">
            <Link href={ROUTES.CARDS}>
              <Button variant="outline" size="sm">Back</Button>
            </Link>
            {card && (
              <Link href={ROUTES.CARD_EDIT(cardNum)}>
                <Button variant="secondary" size="sm">Edit Card</Button>
              </Link>
            )}
          </div>
        </div>

        {error && <Alert variant="error" className="mb-4">{error}</Alert>}

        {card && (
          <div className="space-y-4">
            {/* Card visual */}
            <div className="rounded-2xl bg-gradient-to-br from-blue-800 to-blue-600 p-6 text-white shadow-lg">
              <div className="flex items-start justify-between mb-8">
                <div className="text-xs opacity-75 uppercase tracking-widest">CardDemo</div>
                <StatusBadge
                  status={card.active_status}
                  activeLabel="Active"
                  inactiveLabel="Inactive"
                  className="!text-white !bg-white/20 !ring-white/20"
                />
              </div>
              <div className="font-mono text-xl tracking-widest mb-4">
                {formatCardNumber(card.card_num)}
              </div>
              <div className="flex justify-between items-end">
                <div>
                  <p className="text-xs opacity-75 mb-1">CARD HOLDER</p>
                  <p className="font-semibold text-sm">{card.embossed_name ?? '—'}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs opacity-75 mb-1">EXPIRES</p>
                  <p className="font-semibold text-sm">{formatDate(card.expiration_date)}</p>
                </div>
              </div>
            </div>

            {/* Details */}
            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Card Details</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase">Card Number</p>
                  <p className="text-sm font-mono text-gray-900 mt-1">{card.card_num}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase">Account ID</p>
                  {card.acct_id ? (
                    <Link
                      href={ROUTES.ACCOUNT_VIEW(card.acct_id)}
                      className="text-sm text-blue-600 hover:underline mt-1 block"
                    >
                      {card.acct_id}
                    </Link>
                  ) : (
                    <p className="text-sm text-gray-900 mt-1">—</p>
                  )}
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase">CVV</p>
                  <p className="text-sm text-gray-900 mt-1">***</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase">Status</p>
                  <div className="mt-1"><StatusBadge status={card.active_status} /></div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
