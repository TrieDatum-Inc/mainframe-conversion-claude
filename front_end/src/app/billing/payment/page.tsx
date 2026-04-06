/**
 * Bill Payment page — COBIL00 (BMS map CBIL0A)
 *
 * Route: /billing/payment
 * APIs:
 *   Phase 1: GET /api/v1/billing/{account_id}/balance
 *   Phase 2: POST /api/v1/billing/{account_id}/payment
 * COBOL program: COBIL00C
 *
 * COBIL00C two-phase behavior replicated:
 *   Phase 1 — Display balance:
 *     READ-ACCTDAT-FILE → display ACCT-CURR-BAL as CURBAL
 *     ACCT-CURR-BAL <= 0 → 'You have nothing to pay...'
 *     ACCTIDINI blank → 'Acct ID can NOT be empty...'
 *
 *   Phase 2 — Pay (CONFIRMI='Y' gate):
 *     CONF-PAY-YES path:
 *       READ CXACAIX (card xref) → get card for account
 *       COMPUTE ACCT-CURR-BAL = 0
 *       WRITE new TRANSACT record (type='02', source='POS TERM',
 *             desc='BILL PAYMENT - ONLINE', merchant_id='999999999')
 *       REWRITE ACCTDAT (balance = 0)
 *
 * Bug fix documented:
 *   COBIL00C transaction ID was generated via STARTBR(HIGH-VALUES)+READPREV+ADD-1.
 *   Modern API uses PostgreSQL NEXTVAL — atomic, no race condition.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { getBillingBalance, processPayment, extractError } from '@/lib/api';
import type { BillingBalanceResponse, BillPaymentResponse } from '@/types';
import { formatCurrency } from '@/components/ui/CurrencyDisplay';

type Phase = 'input' | 'balance' | 'confirming' | 'success';

export default function BillPaymentPage() {
  const [accountId, setAccountId] = useState('');
  const [balance, setBalance] = useState<BillingBalanceResponse | null>(null);
  const [payment, setPayment] = useState<BillPaymentResponse | null>(null);
  const [phase, setPhase] = useState<Phase>('input');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Phase 1: COBIL00C READ-ACCTDAT-FILE — check balance
  async function handleCheckBalance(e: React.FormEvent) {
    e.preventDefault();
    if (!accountId.trim()) {
      setError('Acct ID can NOT be empty');
      return;
    }
    if (!/^\d{1,11}$/.test(accountId.trim())) {
      setError('Account ID must be a numeric value (up to 11 digits)');
      return;
    }

    setLoading(true);
    setError('');
    setBalance(null);

    try {
      const data = await getBillingBalance(parseInt(accountId.trim(), 10));
      setBalance(data);
      setPhase('balance');
    } catch (err) {
      const apiErr = extractError(err);
      if (apiErr.error_code === 'ACCOUNT_NOT_FOUND') {
        setError('Account ID NOT found on the file');
      } else {
        setError(apiErr.message);
      }
    } finally {
      setLoading(false);
    }
  }

  // Phase 2: COBIL00C CONF-PAY-YES — process full payment
  async function handleConfirmPayment() {
    setLoading(true);
    setError('');
    setPhase('confirming');

    try {
      const result = await processPayment(parseInt(accountId.trim(), 10), { confirm: 'Y' });
      setPayment(result);
      setPhase('success');
    } catch (err) {
      const apiErr = extractError(err);
      if (apiErr.error_code === 'NOTHING_TO_PAY') {
        setError('You have nothing to pay at this time');
      } else if (apiErr.error_code === 'CARD_NOT_FOUND') {
        setError('No card on file for this account — cannot process payment');
      } else {
        setError(apiErr.message);
      }
      setPhase('balance');
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setAccountId('');
    setBalance(null);
    setPayment(null);
    setPhase('input');
    setError('');
  }

  const currentBal = balance ? parseFloat(balance.current_balance) : 0;
  const hasDebt = !isNaN(currentBal) && currentBal > 0;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Bill Payment</h1>
          <p className="text-sm text-gray-500 mt-1">COBIL00C — pay your account balance</p>
        </div>

        {/* Phase 1: Account ID input */}
        {phase === 'input' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <form onSubmit={handleCheckBalance} className="space-y-4">
              <div>
                <label
                  htmlFor="accountId"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Account ID
                  <span className="text-xs text-gray-400 ml-1">(ACTIDINO — 11 digits)</span>
                </label>
                <input
                  id="accountId"
                  type="text"
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  maxLength={11}
                  placeholder="10000000001"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
                  autoFocus
                />
              </div>

              {error && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Checking...' : 'Check Balance'}
              </button>
            </form>
          </div>
        )}

        {/* Phase 2: Balance display + confirm */}
        {(phase === 'balance' || phase === 'confirming') && balance && (
          <div className="space-y-4">
            {/* Balance card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-sm font-semibold text-gray-500 mb-4">
                Account Balance Summary
              </h2>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-xs text-gray-400">Current Balance</p>
                  <p
                    className={`text-xl font-bold font-mono mt-1 ${
                      currentBal > 0 ? 'text-red-600' : 'text-green-700'
                    }`}
                  >
                    {formatCurrency(balance.current_balance)}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">CURBAL</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Credit Limit</p>
                  <p className="text-xl font-bold font-mono mt-1 text-gray-700">
                    {formatCurrency(balance.credit_limit)}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">CRLIMIT</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Available Credit</p>
                  <p className="text-xl font-bold font-mono mt-1 text-gray-700">
                    {formatCurrency(balance.available_credit)}
                  </p>
                </div>
              </div>
            </div>

            {/* Nothing to pay guard — COBIL00C: ACCT-CURR-BAL <= 0 */}
            {!hasDebt && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-sm text-yellow-800">
                  You have nothing to pay at this time.
                </p>
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Payment confirmation — COBIL00C CONFIRMI='Y' gate */}
            {hasDebt && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-sm font-semibold text-gray-700 mb-2">Confirm Payment</h2>
                <p className="text-sm text-gray-600 mb-4">
                  This will pay your full balance of{' '}
                  <strong className="text-red-600 font-mono">
                    {formatCurrency(balance.current_balance)}
                  </strong>
                  . Your new balance will be{' '}
                  <strong className="text-green-700 font-mono">$0.00</strong>.
                </p>
                <p className="text-xs text-gray-400 mb-4">
                  COBIL00C: COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT → 0.00
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={handleConfirmPayment}
                    disabled={loading}
                    className="flex-1 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                  >
                    {loading ? 'Processing...' : 'Confirm Payment (CONFIRMI=Y)'}
                  </button>
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {!hasDebt && (
              <button
                onClick={handleReset}
                className="w-full py-2 bg-gray-200 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-300"
              >
                Back
              </button>
            )}
          </div>
        )}

        {/* Success */}
        {phase === 'success' && payment && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Payment Successful</h2>
                <p className="text-sm text-gray-500">{payment.message}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 bg-gray-50 rounded-md p-4 text-sm">
              <div>
                <p className="text-xs text-gray-400">Account ID</p>
                <p className="font-mono font-medium">{payment.account_id}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Transaction ID</p>
                <p className="font-mono font-medium">{payment.transaction_id}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Previous Balance</p>
                <p className="font-mono text-red-600 font-medium">
                  {formatCurrency(payment.previous_balance)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-400">New Balance</p>
                <p className="font-mono text-green-700 font-medium">
                  {formatCurrency(payment.new_balance)}
                </p>
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
              >
                Pay Another Account
              </button>
              <Link
                href={`/transactions/view?id=${encodeURIComponent(payment.transaction_id)}`}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-300"
              >
                View Transaction
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
          <Link href="/reports/transactions" className="text-blue-600 hover:underline">
            Reports
          </Link>
        </div>
      </div>
    </div>
  );
}
