/**
 * Card View page — COCRDSL (BMS map CCRDSLA)
 *
 * Route: /cards/view
 * API: GET /api/v1/cards/{card_number}
 * COBOL program: COCRDSLC
 *
 * COCRDSLC read CARDDAT VSAM by card number (RIDFLD), displayed
 * all card fields in ASKIP (read-only) mode.
 *
 * Modern UI:
 *   - Search by card number (CRDNUMI field — MUSTFILL, IC)
 *   - All fields shown read-only
 *   - "Update Card" button links to /cards/update?cardNumber={number}
 *   - cardNumber pre-filled from query param when arriving from list page
 *   - Expiry shown as MM/YYYY computed from expiration_month + expiration_year
 *
 * PF key equivalents:
 *   PF5 (update) → "Update Card" button
 *   PF3 (exit)   → "Back" button
 *
 * Note: CardDetailResponse fields are card_embossed_name (not embossed_name),
 *       expiration_month + expiration_year (not expiration_date as a string).
 *       card_number_masked is not in detail response — derive from card_number.
 */

'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { getCard, extractError } from '@/lib/api';
import type { CardDetailResponse } from '@/types';
import StatusBadge from '@/components/ui/StatusBadge';
import { MessageBar } from '@/components/ui/MessageBar';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

/** Mask card number — show only last 4 digits (PCI-DSS). */
function maskCardNumber(cardNumber: string): string {
  if (!cardNumber || cardNumber.length < 4) return cardNumber;
  return `${'*'.repeat(cardNumber.length - 4)}${cardNumber.slice(-4)}`;
}

/** Format expiry as MM/YYYY for display. */
function formatExpiry(month: number, year: number): string {
  return `${String(month).padStart(2, '0')}/${year}`;
}

function CardViewContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const paramCardNumber = searchParams.get('cardNumber') || '';

  const [cardNumber, setCardNumber] = useState(paramCardNumber);
  const [card, setCard] = useState<CardDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Auto-load if card number provided via query param (e.g. from list row click)
  useEffect(() => {
    if (paramCardNumber) {
      loadCard(paramCardNumber);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramCardNumber]);

  async function loadCard(num: string) {
    const trimmed = num.trim();
    if (!trimmed) {
      setError('Card number cannot be empty');
      return;
    }
    if (!/^\d{1,16}$/.test(trimmed)) {
      setError('Card number must be numeric (up to 16 digits)');
      return;
    }

    setLoading(true);
    setError('');
    setCard(null);

    try {
      const data = await getCard(trimmed);
      setCard(data);
    } catch (err) {
      const apiErr = extractError(err);
      setError(apiErr.message);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    loadCard(cardNumber);
  }

  function handleClear() {
    setCardNumber('');
    setCard(null);
    setError('');
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <div className="bg-blue-900 text-white px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-yellow-300">CardDemo</h1>
            <p className="text-sm text-blue-200">Credit Card Demo Application</p>
          </div>
          <div className="text-sm text-blue-200">
            <span className="font-medium text-white">COCRDSL</span> — Card View
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-6">
        {/* Search form */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">View Credit Card</h2>
          <form onSubmit={handleSearch} className="flex gap-3 items-end">
            <div className="flex-1">
              <label htmlFor="cardNumber" className="block text-sm font-medium text-gray-700 mb-1">
                Card Number
                <span className="text-red-500 ml-1">*</span>
              </label>
              <input
                id="cardNumber"
                type="text"
                value={cardNumber}
                onChange={(e) => setCardNumber(e.target.value)}
                maxLength={16}
                placeholder="16-digit card number"
                autoFocus={!paramCardNumber}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                           font-mono tracking-widest"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium
                         hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : 'View Card'}
            </button>
            <button
              type="button"
              onClick={handleClear}
              className="px-6 py-2 bg-gray-100 text-gray-700 rounded-md text-sm font-medium
                         hover:bg-gray-200 border border-gray-300"
            >
              Clear
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-2 bg-gray-100 text-gray-700 rounded-md text-sm font-medium
                         hover:bg-gray-200 border border-gray-300"
            >
              Back
            </button>
          </form>
        </div>

        {error && <MessageBar message={error} color="red" className="mb-4" />}

        {loading && (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        )}

        {/* Card detail — all ASKIP fields from CCRDSLA BMS map */}
        {card && !loading && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h3 className="text-base font-semibold text-gray-900 font-mono">
                  {maskCardNumber(card.card_number)}
                </h3>
                <StatusBadge status={card.active_status} />
              </div>
              {/* PF5 Update equivalent */}
              <Link
                href={`/cards/update?cardNumber=${encodeURIComponent(card.card_number)}`}
                className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-md
                           hover:bg-blue-700 font-medium"
              >
                PF5 — Update Card
              </Link>
            </div>

            <div className="px-6 py-4 grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-4">
              {/* CARDSID — card number full (admin view) */}
              <ReadOnlyField
                label="Card Number (Full)"
                value={card.card_number}
                mono
              />
              {/* ACCTSID — PROT field, cannot be changed */}
              <ReadOnlyField
                label="Account ID"
                value={String(card.account_id)}
              />
              {/* Customer ID */}
              <ReadOnlyField
                label="Customer ID"
                value={String(card.customer_id)}
              />
              {/* CRDNAME — embossed cardholder name */}
              <ReadOnlyField
                label="Embossed Name"
                value={card.card_embossed_name || '—'}
              />
              {/* EXPMON + EXPYEAR — expiry date */}
              <ReadOnlyField
                label="Expiry Date"
                value={
                  card.expiration_month && card.expiration_year
                    ? formatExpiry(card.expiration_month, card.expiration_year)
                    : '—'
                }
              />
              {/* CRDSTCD — active status Y/N displayed as badge above */}
              <ReadOnlyField
                label="Status Code"
                value={card.active_status}
              />
            </div>

            <div className="px-6 py-3 bg-gray-50 rounded-b-lg border-t border-gray-100">
              <p className="text-xs text-gray-400">
                Last updated: {new Date(card.updated_at).toLocaleString()}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function CardViewPage() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center items-center min-h-screen">
          <LoadingSpinner />
        </div>
      }
    >
      <CardViewContent />
    </Suspense>
  );
}

/** Read-only field — maps DFHMDF ASKIP on CCRDSLA map. */
function ReadOnlyField({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-sm font-medium text-gray-900 mt-0.5 ${mono ? 'font-mono' : ''}`}>
        {value}
      </p>
    </div>
  );
}
