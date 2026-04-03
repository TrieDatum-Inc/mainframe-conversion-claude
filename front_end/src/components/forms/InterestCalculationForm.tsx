'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { calculateInterest } from '@/lib/api'
import { AlertBanner } from '@/components/ui/AlertBanner'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { formatCurrency, todayISOString } from '@/lib/utils'
import type { InterestCalculationResponse } from '@/types'

interface FormValues {
  run_date: string
}

/**
 * Interest Calculation Form — CBACT04C UI equivalent.
 *
 * Maps JCL PARM (run date) to form input.
 * Displays per-account interest summaries and created transactions.
 * Fee calculation note preserved (1400-COMPUTE-FEES stub).
 */
export function InterestCalculationForm() {
  const [result, setResult] = useState<InterestCalculationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    defaultValues: { run_date: todayISOString() },
  })

  async function onSubmit(data: FormValues) {
    setError(null)
    setResult(null)
    setIsLoading(true)
    try {
      const response = await calculateInterest(data)
      setResult(response)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unexpected error')
    } finally {
      setIsLoading(false)
    }
  }

  const totalInterest = result?.account_summaries.reduce(
    (sum, s) => sum + parseFloat(String(s.total_interest)),
    0
  ) ?? 0

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">
          Interest Calculation
        </h2>
        <p className="text-sm text-gray-500 mb-1">
          CBACT04C — Calculates monthly interest for all accounts using disclosure group rates.
        </p>
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2 mb-6">
          Note: Fee calculation (1400-COMPUTE-FEES) is not implemented — this was a stub in the
          original COBOL program.
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="form-label" htmlFor="run_date">
              Run Date (JCL PARM-DATE) <span className="text-red-500">*</span>
            </label>
            <p className="text-xs text-gray-500 mb-1">
              Used as prefix for generated interest transaction IDs.
              Format: YYYYMMDD + 6-digit suffix = 16-char TRAN-ID
            </p>
            <input
              id="run_date"
              type="date"
              className="form-input md:w-1/3"
              {...register('run_date', { required: 'Run date is required' })}
            />
            {errors.run_date && (
              <p className="form-error">{errors.run_date.message}</p>
            )}
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-800">
            <p className="font-medium mb-1">Interest Formula (CBACT04C 1300-COMPUTE-INTEREST)</p>
            <p className="font-mono">Monthly Interest = (Category Balance × Annual Rate) / 1200</p>
            <p className="mt-1">Falls back to DEFAULT disclosure group when specific group rate not found.</p>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading}
          >
            {isLoading ? 'Calculating...' : 'Run Interest Calculation'}
          </button>
        </form>
      </div>

      {isLoading && (
        <LoadingSpinner message="Calculating interest across all accounts..." />
      )}

      {error && <AlertBanner type="error" title="Calculation Failed" message={error} />}

      {result && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Calculation Summary</h3>
              <StatusBadge status={result.status} />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-center">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-2xl font-bold text-gray-900">{result.accounts_processed}</p>
                <p className="text-xs text-gray-500">Accounts Processed</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-3">
                <p className="text-2xl font-bold text-blue-700">
                  {result.interest_transactions_created}
                </p>
                <p className="text-xs text-gray-500">Transactions Created</p>
              </div>
              <div className="bg-green-50 rounded-lg p-3">
                <p className="text-xl font-bold text-green-700">
                  {formatCurrency(totalInterest)}
                </p>
                <p className="text-xs text-gray-500">Total Interest</p>
              </div>
            </div>

            <p className="text-sm text-gray-500 mt-3">Run date: {result.run_date}</p>
          </div>

          {/* Per-account summaries */}
          {result.account_summaries.length > 0 && (
            <div className="card p-6">
              <h4 className="font-medium text-gray-900 mb-4">Account Interest Summaries</h4>
              <div className="space-y-3">
                {result.account_summaries.map((summary) => (
                  <details key={summary.acct_id} className="border border-gray-200 rounded-lg">
                    <summary className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-sm">{summary.acct_id}</span>
                        <span className="text-xs text-gray-500">
                          {summary.category_count} categories
                        </span>
                      </div>
                      <span className="font-medium text-blue-700">
                        {formatCurrency(summary.total_interest)} interest
                      </span>
                    </summary>
                    <div className="p-3 border-t border-gray-100">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="text-gray-500 text-left">
                            <th className="pb-1">Transaction ID</th>
                            <th className="pb-1">Balance</th>
                            <th className="pb-1">Rate</th>
                            <th className="pb-1 text-right">Interest</th>
                          </tr>
                        </thead>
                        <tbody>
                          {summary.transactions_created.map((t) => (
                            <tr key={t.tran_id} className="border-t border-gray-100">
                              <td className="py-1 font-mono">{t.tran_id}</td>
                              <td className="py-1">{formatCurrency(t.balance)}</td>
                              <td className="py-1">{t.interest_rate}%</td>
                              <td className="py-1 text-right text-blue-700 font-medium">
                                {formatCurrency(t.monthly_interest)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </details>
                ))}
              </div>
            </div>
          )}

          <p className="text-sm text-gray-500 card p-3">{result.message}</p>
        </div>
      )}
    </div>
  )
}
