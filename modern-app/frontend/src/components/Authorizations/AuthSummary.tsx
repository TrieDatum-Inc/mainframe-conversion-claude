"use client";

/**
 * AuthSummary Component
 *
 * Displays account-level authorization summary at the top of the page.
 * Maps to COPAU00 BMS screen rows 5-12:
 *   - Customer name, customer ID
 *   - Address info
 *   - Credit/cash limits and balances
 *   - Approved/declined counts and amounts
 */

import type { AuthorizationSummary } from "@/types";
import { getAccountStatusClasses, getAuthStatusLabel, formatCurrency } from "@/lib/utils";

interface AuthSummaryProps {
  summary: AuthorizationSummary;
}

export function AuthSummary({ summary }: AuthSummaryProps) {
  const statusClass = getAccountStatusClasses(summary.auth_status);

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Account Summary</h2>
        <span className={`text-sm px-3 py-1 rounded-full font-medium ${statusClass} bg-opacity-10`}>
          {getAuthStatusLabel(summary.auth_status)}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Account Identifiers */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm text-gray-500">Account ID</span>
            <span className="text-sm font-mono font-medium text-gray-900">
              {summary.account_id}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-500">Customer ID</span>
            <span className="text-sm font-mono text-gray-700">{summary.customer_id}</span>
          </div>
        </div>

        {/* Credit Limits */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm text-gray-500">Credit Limit</span>
            <span className="text-sm font-medium text-gray-900">
              {formatCurrency(summary.credit_limit)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-500">Cash Limit</span>
            <span className="text-sm font-medium text-gray-900">
              {formatCurrency(summary.cash_limit)}
            </span>
          </div>
        </div>

        {/* Balances */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm text-gray-500">Credit Balance</span>
            <span className="text-sm font-medium text-gray-900">
              {formatCurrency(summary.credit_balance)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-500">Cash Balance</span>
            <span className="text-sm font-medium text-gray-900">
              {formatCurrency(summary.cash_balance)}
            </span>
          </div>
        </div>

        {/* Auth Counts and Amounts */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm text-gray-500">
              Approvals ({summary.approved_count})
            </span>
            <span className="text-sm font-medium text-green-700">
              {formatCurrency(summary.approved_amount)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-500">
              Declines ({summary.declined_count})
            </span>
            <span className="text-sm font-medium text-red-700">
              {formatCurrency(summary.declined_amount)}
            </span>
          </div>
        </div>
      </div>

      {/* Available Credit Bar */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Available Credit</span>
          <span>
            {formatCurrency(
              String(
                Math.max(
                  0,
                  parseFloat(summary.credit_limit) - parseFloat(summary.credit_balance)
                )
              )
            )}
          </span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all"
            style={{
              width: `${Math.min(
                100,
                (parseFloat(summary.credit_balance) / parseFloat(summary.credit_limit)) * 100
              )}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
}
