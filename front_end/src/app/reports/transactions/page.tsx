/**
 * Transaction Reports page — CORPT00 (BMS map CRPT0A)
 *
 * Route: /reports/transactions
 * APIs:
 *   POST /api/v1/reports/request     → 202 Accepted
 *   GET  /api/v1/reports/{report_id} → status polling
 * COBOL program: CORPT00C
 *
 * CORPT00C behavior replicated:
 *   - Report type selection: MONTHLYI='M', YEARLYI='Y', CUSTOMI='C'
 *   - CONFIRMI='Y' gate before WRITEQ TD QUEUE='JOBS'
 *   - CALCULATE-END-DATE: if custom end_date blank → last day of prior month
 *   - Custom report: start_date + end_date required
 *
 * Modern additions (CORPT00C had no status tracking):
 *   - 202 Accepted response with request_id
 *   - Status polling via GET /reports/{report_id}
 *   - Status display: PENDING → RUNNING → COMPLETED / FAILED
 *
 * CORPT00C CALCULATE-END-DATE logic:
 *   FUNCTION DATE-OF-INTEGER(FUNCTION INTEGER-OF-DATE(WS-CURDATE-N) - 1)
 *   = first day of current month - 1 day = last day of prior month
 *   This is handled server-side; client sends null end_date for 'C' type.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { requestReport, getReportStatus, extractError } from '@/lib/api';
import type { ReportRequestResponse, ReportStatusResponse } from '@/types';

type ReportType = 'M' | 'Y' | 'C';

export default function TransactionReportsPage() {
  const [reportType, setReportType] = useState<ReportType>('M');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState<ReportRequestResponse | null>(null);
  const [statusData, setStatusData] = useState<ReportStatusResponse | null>(null);
  const [pollingStatus, setPollingStatus] = useState(false);
  const [statusError, setStatusError] = useState('');

  function validateDates(): string | null {
    if (reportType === 'C') {
      if (!startDate) return 'Start date is required for custom reports';
      if (startDate && endDate && endDate < startDate) {
        return 'End date must not be before start date';
      }
    }
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');

    const dateErr = validateDates();
    if (dateErr) {
      setError(dateErr);
      return;
    }

    setSubmitting(true);

    try {
      const payload: Parameters<typeof requestReport>[0] = {
        report_type: reportType,
        confirm: 'Y',
      };

      if (reportType === 'C') {
        if (startDate) payload.start_date = startDate;
        if (endDate) payload.end_date = endDate;
        // blank end_date → server uses CALCULATE-END-DATE (last day prior month)
      }

      const result = await requestReport(payload);
      setSubmitted(result);
      setStatusData(null);
      setStatusError('');
    } catch (err) {
      const apiErr = extractError(err);
      setError(apiErr.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCheckStatus() {
    if (!submitted) return;
    setPollingStatus(true);
    setStatusError('');

    try {
      const status = await getReportStatus(submitted.request_id);
      setStatusData(status);
    } catch (err) {
      const apiErr = extractError(err);
      setStatusError(apiErr.message);
    } finally {
      setPollingStatus(false);
    }
  }

  function handleReset() {
    setReportType('M');
    setStartDate('');
    setEndDate('');
    setSubmitted(null);
    setStatusData(null);
    setError('');
    setStatusError('');
  }

  const statusColor = {
    PENDING: 'text-yellow-700 bg-yellow-50 border-yellow-200',
    RUNNING: 'text-blue-700 bg-blue-50 border-blue-200',
    COMPLETED: 'text-green-700 bg-green-50 border-green-200',
    FAILED: 'text-red-700 bg-red-50 border-red-200',
  } as const;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Transaction Reports</h1>
          <p className="text-sm text-gray-500 mt-1">
            CORPT00C — submit a report generation request
          </p>
        </div>

        {/* Success — report submitted */}
        {submitted ? (
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-start gap-3 mb-4">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-base font-semibold text-gray-900">Report Request Submitted</h2>
                  <p className="text-sm text-gray-500 mt-0.5">{submitted.message}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 bg-gray-50 rounded-md p-4 text-sm">
                <div>
                  <p className="text-xs text-gray-400">Request ID</p>
                  <p className="font-mono font-medium">{submitted.request_id}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Report Type</p>
                  <p className="font-medium">
                    {submitted.report_type === 'M'
                      ? 'Monthly'
                      : submitted.report_type === 'Y'
                      ? 'Yearly'
                      : 'Custom'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Period Start</p>
                  <p className="font-mono">{submitted.start_date || 'Auto-calculated'}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Period End</p>
                  <p className="font-mono">{submitted.end_date || 'Auto-calculated'}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Initial Status</p>
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-xs font-medium border ${
                      statusColor[submitted.status] || 'text-gray-700 bg-gray-50 border-gray-200'
                    }`}
                  >
                    {submitted.status}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Requested At</p>
                  <p className="text-xs">{new Date(submitted.requested_at).toLocaleString()}</p>
                </div>
              </div>

              <p className="text-xs text-gray-400 mt-3">
                CORPT00C: replaces WRITEQ TD QUEUE=&apos;JOBS&apos; — report generated asynchronously.
                Use the Check Status button to poll for completion.
              </p>
            </div>

            {/* Status polling */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-700">Report Status</h3>
                <button
                  onClick={handleCheckStatus}
                  disabled={pollingStatus}
                  className="px-3 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {pollingStatus ? 'Checking...' : 'Check Status'}
                </button>
              </div>

              {statusError && (
                <p className="text-sm text-red-600">{statusError}</p>
              )}

              {statusData && (
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium border ${
                        statusColor[statusData.status] || 'text-gray-700 bg-gray-50 border-gray-200'
                      }`}
                    >
                      {statusData.status}
                    </span>
                    {statusData.completed_at && (
                      <span className="text-xs text-gray-400">
                        Completed: {new Date(statusData.completed_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                  {statusData.result_path && (
                    <p className="text-xs text-gray-600">
                      Result: <span className="font-mono">{statusData.result_path}</span>
                    </p>
                  )}
                  {statusData.error_message && (
                    <p className="text-xs text-red-600">Error: {statusData.error_message}</p>
                  )}
                </div>
              )}
            </div>

            <button
              onClick={handleReset}
              className="w-full py-2 bg-gray-200 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-300"
            >
              Submit Another Report
            </button>
          </div>
        ) : (
          /* Request form */
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Report type — MONTHLYI / YEARLYI / CUSTOMI */}
              <div>
                <fieldset>
                  <legend className="text-sm font-semibold text-gray-700 mb-3">
                    Report Type
                    <span className="text-xs text-gray-400 font-normal ml-2">
                      (CORPT00C: M/Y/C selection)
                    </span>
                  </legend>
                  <div className="space-y-2">
                    {(
                      [
                        { value: 'M', label: 'Monthly', hint: 'Current month (auto dates)' },
                        { value: 'Y', label: 'Yearly', hint: 'Current year (auto dates)' },
                        {
                          value: 'C',
                          label: 'Custom',
                          hint: 'Specify date range (CUSTOMI)',
                        },
                      ] as const
                    ).map((opt) => (
                      <label
                        key={opt.value}
                        className={`flex items-start gap-3 p-3 border rounded-md cursor-pointer ${
                          reportType === opt.value
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <input
                          type="radio"
                          value={opt.value}
                          checked={reportType === opt.value}
                          onChange={() => setReportType(opt.value)}
                          className="mt-0.5"
                        />
                        <div>
                          <span className="text-sm font-medium text-gray-800">{opt.label}</span>
                          <span className="text-xs text-gray-400 ml-2">{opt.hint}</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </fieldset>
              </div>

              {/* Custom date range — only shown when type = 'C' */}
              {reportType === 'C' && (
                <div className="border border-dashed border-gray-300 rounded-md p-4 space-y-3">
                  <p className="text-xs text-gray-500 font-medium">
                    CORPT00C CUSTOMI: SDTYYYY1I + SDTMMI + SDTDDI / EDTYYYY1I + EDTMMI + EDTDDI
                  </p>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Start Date *
                      </label>
                      <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        End Date
                        <span className="text-gray-400 ml-1">
                          (blank → CALCULATE-END-DATE)
                        </span>
                      </label>
                      <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                      <p className="text-xs text-gray-400 mt-0.5">
                        Leave blank: server computes last day of prior month
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Auto-derived date info for M and Y */}
              {reportType === 'M' && (
                <div className="text-xs text-gray-500 bg-blue-50 border border-blue-100 rounded p-3">
                  CORPT00C MONTHLYI: Date range = first day of current month → today.
                  Dates are automatically derived on the server.
                </div>
              )}
              {reportType === 'Y' && (
                <div className="text-xs text-gray-500 bg-blue-50 border border-blue-100 rounded p-3">
                  CORPT00C YEARLYI: Date range = January 1 → December 31 of current year.
                  Dates are automatically derived on the server.
                </div>
              )}

              {/* Confirmation */}
              <div className="text-xs text-gray-500 bg-yellow-50 border border-yellow-200 rounded p-3">
                CORPT00C CONFIRMI: By clicking &apos;Submit Report&apos; you confirm (CONFIRMI=&apos;Y&apos;)
                and the report will be queued for generation.
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2.5 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? 'Submitting...' : 'Submit Report Request (CONFIRMI=Y)'}
              </button>
            </form>
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
          <Link href="/billing/payment" className="text-blue-600 hover:underline">
            Bill Payment
          </Link>
        </div>
      </div>
    </div>
  );
}
