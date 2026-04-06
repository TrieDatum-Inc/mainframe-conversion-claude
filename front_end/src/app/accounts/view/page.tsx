/**
 * Account View page — COACTVW (BMS map CACTVWA)
 *
 * Route: /accounts/view
 * API: GET /api/v1/accounts/{account_id}
 * COBOL program: COACTVWC
 *
 * Replaces the COACTVWC transaction which:
 *   1. READ ACCTDAT by ACCT-ID
 *   2. READ CUSTDAT via account_customer_xref
 *   3. READ CARDAIX (AIX on account_id) for associated cards
 *
 * Modern UI design:
 *   - Search field at top (ACCTSID on CACTVWA map — MUSTFILL, IC)
 *   - Account summary card with financial data
 *   - Customer info card with masked SSN
 *   - "Update Account" action link navigating to /accounts/update
 *   - Currency formatted with Intl.NumberFormat (replaces PICOUT='+ZZZ,ZZZ,ZZZ.99')
 *   - NOT a 3270 replica — modern card-based layout
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { getAccount, extractError } from '@/lib/api';
import type { AccountViewResponse } from '@/types';
import CurrencyDisplay from '@/components/ui/CurrencyDisplay';
import StatusBadge from '@/components/ui/StatusBadge';
import { MessageBar } from '@/components/ui/MessageBar';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function AccountViewPage() {
  const router = useRouter();
  const [accountId, setAccountId] = useState('');
  const [account, setAccount] = useState<AccountViewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!accountId.trim()) {
      setError('Account ID cannot be empty');
      return;
    }
    if (!/^\d{1,11}$/.test(accountId.trim())) {
      setError('Account ID must be a numeric value up to 11 digits');
      return;
    }

    setLoading(true);
    setError('');
    setAccount(null);

    try {
      const data = await getAccount(parseInt(accountId.trim(), 10));
      setAccount(data);
    } catch (err) {
      const apiErr = extractError(err);
      setError(apiErr.message);
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    setAccountId('');
    setAccount(null);
    setError('');
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <div className="bg-blue-900 text-white px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-yellow-300">CardDemo</h1>
            <p className="text-sm text-blue-200">Credit Card Demo Application</p>
          </div>
          <div className="text-sm text-blue-200">
            <span className="font-medium text-white">COACTVW</span> — Account View
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-6">
        {/* Search form */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">View Account</h2>
          <form onSubmit={handleSearch} className="flex gap-3 items-end">
            <div className="flex-1">
              <label htmlFor="accountId" className="block text-sm font-medium text-gray-700 mb-1">
                Account ID
                <span className="text-red-500 ml-1">*</span>
              </label>
              <input
                id="accountId"
                type="text"
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                maxLength={11}
                placeholder="11-digit account number"
                autoFocus
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                           font-mono text-green-700"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium
                         hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : 'View Account'}
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

        {/* Error message */}
        {error && (
          <MessageBar message={error} color="red" className="mb-4" />
        )}

        {loading && (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        )}

        {/* Account data */}
        {account && !loading && (
          <div className="space-y-6">
            {/* Account Summary */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-base font-semibold text-gray-900">
                  Account #{account.account_id}
                </h3>
                <div className="flex items-center gap-3">
                  <StatusBadge status={account.active_status} />
                  <Link
                    href={`/accounts/update?accountId=${account.account_id}`}
                    className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-md
                               hover:bg-blue-700 font-medium"
                  >
                    Update Account
                  </Link>
                </div>
              </div>
              <div className="px-6 py-4 grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-4">
                <ReadOnlyField label="Open Date" value={account.open_date || '—'} />
                <ReadOnlyField label="Expiry Date" value={account.expiration_date || '—'} />
                <ReadOnlyField label="Reissue Date" value={account.reissue_date || '—'} />
                <ReadOnlyField label="Account Group" value={account.group_id || '—'} />
              </div>
              <div className="px-6 pb-4 grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-4 border-t border-gray-100 pt-4">
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Credit Limit</p>
                  <CurrencyDisplay amount={account.credit_limit} className="text-base font-semibold" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Cash Credit Limit</p>
                  <CurrencyDisplay amount={account.cash_credit_limit} className="text-base font-semibold" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Current Balance</p>
                  <CurrencyDisplay amount={account.current_balance} className="text-base font-semibold" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Cycle Credit</p>
                  <CurrencyDisplay amount={account.curr_cycle_credit} className="text-base" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Cycle Debit</p>
                  <CurrencyDisplay amount={account.curr_cycle_debit} className="text-base" />
                </div>
              </div>
            </div>

            {/* Customer Details */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-base font-semibold text-gray-900">
                  Customer Information
                </h3>
              </div>
              <div className="px-6 py-4 grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-4">
                <ReadOnlyField
                  label="Customer ID"
                  value={String(account.customer.customer_id)}
                />
                <ReadOnlyField
                  label="SSN (Masked)"
                  value={account.customer.ssn_masked}
                />
                <ReadOnlyField
                  label="Date of Birth"
                  value={account.customer.date_of_birth || '—'}
                />
                <ReadOnlyField
                  label="FICO Score"
                  value={account.customer.fico_score != null ? String(account.customer.fico_score) : '—'}
                />
                <ReadOnlyField
                  label="Primary Card Holder"
                  value={account.customer.primary_card_holder}
                />
              </div>
              <div className="px-6 py-4 grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-4 border-t border-gray-100">
                <ReadOnlyField
                  label="First Name"
                  value={account.customer.first_name}
                />
                <ReadOnlyField
                  label="Middle Name"
                  value={account.customer.middle_name || '—'}
                />
                <ReadOnlyField
                  label="Last Name"
                  value={account.customer.last_name}
                />
                <ReadOnlyField
                  label="Address Line 1"
                  value={account.customer.address_line_1 || '—'}
                />
                <ReadOnlyField
                  label="Address Line 2"
                  value={account.customer.address_line_2 || '—'}
                />
                <ReadOnlyField
                  label="City"
                  value={account.customer.city || '—'}
                />
                <ReadOnlyField
                  label="State"
                  value={account.customer.state_code || '—'}
                />
                <ReadOnlyField
                  label="ZIP Code"
                  value={account.customer.zip_code || '—'}
                />
                <ReadOnlyField
                  label="Country"
                  value={account.customer.country_code || '—'}
                />
                <ReadOnlyField
                  label="Phone 1"
                  value={account.customer.phone_1 || '—'}
                />
                <ReadOnlyField
                  label="Phone 2"
                  value={account.customer.phone_2 || '—'}
                />
                <ReadOnlyField
                  label="Govt ID Ref"
                  value={account.customer.government_id_ref || '—'}
                />
                <ReadOnlyField
                  label="EFT Account ID"
                  value={account.customer.eft_account_id || '—'}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/** Read-only field display — maps DFHMDF ASKIP fields on CACTVWA map. */
function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-sm font-medium text-gray-900 mt-0.5">{value}</p>
    </div>
  );
}
