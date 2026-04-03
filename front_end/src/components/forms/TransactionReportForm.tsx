'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { generateTransactionReport } from '@/lib/api'
import { AlertBanner } from '@/components/ui/AlertBanner'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { formatCurrency, formatDateTime, todayISOString } from '@/lib/utils'
import type { TransactionReportResponse } from '@/types'

interface FormValues {
  start_date: string
  end_date: string
}

/**
 * Transaction Report Form — CBTRN03C UI equivalent.
 *
 * Maps DATEPARM control file (start/end dates) to form inputs.
 * Displays 133-char report text in monospace, matching CBTRN03C DALYREPT format.
 */
export function TransactionReportForm() {
  const [result, setResult] = useState<TransactionReportResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showRawReport, setShowRawReport] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    defaultValues: {
      start_date: todayISOString(),
      end_date: todayISOString(),
    },
  })

  async function onSubmit(data: FormValues) {
    setError(null)
    setResult(null)
    setIsLoading(true)
    try {
      const response = await generateTransactionReport(data)
      setResult(response)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unexpected error')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">
          Transaction Detail Report
        </h2>
        <p className="text-sm text-gray-500 mb-6">
          CBTRN03C — Generates DALYREPT report for a date range.
          Missing reference data is logged (not abended). Page size: 20 lines.
        </p>

        {/* Date range — maps to DATEPARM control file */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="form-label" htmlFor="start_date">
                Start Date (WS-START-DATE) <span className="text-red-500">*</span>
              </label>
              <input
                id="start_date"
                type="date"
                className="form-input"
                {...register('start_date', { required: 'Start date is required' })}
              />
              {errors.start_date && (
                <p className="form-error">{errors.start_date.message}</p>
              )}
            </div>

            <div>
              <label className="form-label" htmlFor="end_date">
                End Date (WS-END-DATE) <span className="text-red-500">*</span>
              </label>
              <input
                id="end_date"
                type="date"
                className="form-input"
                {...register('end_date', { required: 'End date is required' })}
              />
              {errors.end_date && (
                <p className="form-error">{errors.end_date.message}</p>
              )}
            </div>
          </div>

          {/* PF keys -> action buttons */}
          <div className="flex gap-3">
            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading}
              aria-label="Generate report (ENTER key equivalent)"
            >
              {isLoading ? 'Generating...' : 'Generate Report'}
            </button>
            <button
              type="reset"
              className="btn-secondary"
              aria-label="Clear form (PF3 equivalent)"
            >
              Clear (PF3)
            </button>
          </div>
        </form>
      </div>

      {isLoading && <LoadingSpinner message="Generating DALYREPT report..." />}

      {error && <AlertBanner type="error" title="Report Generation Failed" message={error} />}

      {result && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">DALYREPT Summary</h3>
              <StatusBadge status={result.status} />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center mb-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xl font-bold text-gray-900">{result.totals.transaction_count}</p>
                <p className="text-xs text-gray-500">Transactions</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-3">
                <p className="text-xl font-bold text-blue-700">
                  {formatCurrency(result.totals.grand_total)}
                </p>
                <p className="text-xs text-gray-500">Grand Total</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xl font-bold text-gray-900">{result.totals.page_count}</p>
                <p className="text-xs text-gray-500">Pages</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-sm font-medium text-gray-700">
                  {result.start_date} to {result.end_date}
                </p>
                <p className="text-xs text-gray-500">Date Range</p>
              </div>
            </div>
          </div>

          {/* Detail lines table */}
          {result.report_lines.length > 0 && (
            <div className="card p-6">
              <h4 className="font-medium text-gray-900 mb-4">Transaction Details</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-left text-xs text-gray-600">
                      <th className="p-2 font-medium">Transaction ID</th>
                      <th className="p-2 font-medium">Account ID</th>
                      <th className="p-2 font-medium">Type</th>
                      <th className="p-2 font-medium">Category</th>
                      <th className="p-2 font-medium">Source</th>
                      <th className="p-2 font-medium text-right">Amount</th>
                      <th className="p-2 font-medium">Processed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.report_lines.map((line) => (
                      <tr key={line.tran_id} className="border-t border-gray-100 hover:bg-gray-50">
                        <td className="p-2 font-mono text-xs">{line.tran_id}</td>
                        <td className="p-2 font-mono text-xs">{line.account_id}</td>
                        <td className="p-2 text-xs">
                          <span className="font-mono">{line.tran_type_cd}</span>
                          {' - '}
                          {/* Truncated to 15 chars per CBTRN03C TRAN-REPORT-TYPE-DESC */}
                          {line.tran_type_desc.substring(0, 15)}
                        </td>
                        <td className="p-2 text-xs">
                          <span className="font-mono">{line.tran_cat_cd}</span>
                          {' - '}
                          {/* Truncated to 29 chars per CBTRN03C TRAN-REPORT-CAT-DESC */}
                          {line.tran_cat_desc.substring(0, 29)}
                        </td>
                        <td className="p-2 text-xs">{line.tran_source}</td>
                        <td className={`p-2 text-xs text-right font-mono ${
                          parseFloat(String(line.tran_amt)) < 0
                            ? 'text-red-700'
                            : 'text-green-700'
                        }`}>
                          {formatCurrency(line.tran_amt)}
                        </td>
                        <td className="p-2 text-xs text-gray-500">
                          {formatDateTime(line.tran_proc_ts)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Raw report text — preserves CBTRN03C 133-char report format */}
          <div className="card p-6">
            <button
              type="button"
              onClick={() => setShowRawReport(!showRawReport)}
              className="btn-secondary mb-4"
            >
              {showRawReport ? 'Hide' : 'Show'} DALYREPT Raw Output
            </button>
            {showRawReport && (
              <pre className="report-output text-xs">
                {result.report_text}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
