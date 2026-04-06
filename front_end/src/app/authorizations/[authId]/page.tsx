'use client';

/**
 * Authorization Detail Page — replaces BMS map COPAU1A (mapset COPAU01).
 * Route: /authorizations/[authId]
 * COBOL program: COPAUS1C (transaction CPVD)
 *
 * Features (maps COPAUS1C behavior):
 *   - Full read-only detail view of single authorization (all COPAU01 fields)
 *   - Fraud status with color coding (N=green, F=red, R=yellow)
 *   - Fraud toggle button with confirmation dialog (maps PF5 → COPAUS2C LINK)
 *   - Back button to authorization list (maps PF3 → XCTL COPAUS0C)
 *   - Error messages (ERRMSG field, row 23, RED)
 *   - Fraud audit log section (DB2 CARDDEMO.AUTHFRDS)
 *
 * NOTE: This page uses [authId] (camelCase) per Next.js App Router conventions.
 * The spec shows /authorizations/[authId]/page.tsx for detail view.
 */

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  getAuthorizationDetail,
  getFraudLogs,
  toggleFraudFlag,
  ApiClientError,
} from '@/lib/api';
import type {
  AuthDetailResponse,
  AuthFraudLogResponse,
  FraudToggleResponse,
} from '@/types/authorization';
import { FRAUD_STATUS_CONFIG } from '@/types/authorization';
import { AuthorizationDetailCard } from '@/components/authorizations/AuthorizationDetailCard';
import { FraudStatusBadge } from '@/components/authorizations/FraudStatusBadge';
import { formatCurrency } from '@/lib/utils';

export default function AuthorizationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const authId = Number(params.authId);

  const [detail, setDetail] = useState<AuthDetailResponse | null>(null);
  const [fraudLogs, setFraudLogs] = useState<AuthFraudLogResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isFraudToggling, setIsFraudToggling] = useState(false);
  // COPAUS1C: WS-MESSAGE → ERRMSG field (row 23, RED)
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  // Confirmation dialog state (maps PF5 → confirmation before COPAUS2C LINK)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  const loadDetail = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage('');
    try {
      const [detailData, logsData] = await Promise.all([
        getAuthorizationDetail(authId),
        getFraudLogs(authId),
      ]);
      setDetail(detailData);
      setFraudLogs(logsData);
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 404) {
          setErrorMessage(`Authorization ${authId} not found.`);
        } else if (err.status === 401) {
          router.push('/login');
        } else {
          setErrorMessage(err.apiError.message);
        }
      } else {
        setErrorMessage('Failed to load authorization details.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [authId, router]);

  useEffect(() => {
    if (!isNaN(authId)) {
      void loadDetail();
    }
  }, [authId, loadDetail]);

  /**
   * PF5 — Mark/Remove Fraud.
   * Replaces: COPAUS1C MARK-AUTH-FRAUD → EXEC CICS LINK COPAUS2C.
   * 3-state cycle: N→F, F→R, R→F
   * Shows confirmation dialog before executing.
   */
  async function handleFraudToggleConfirm() {
    if (!detail) return;
    setShowConfirmDialog(false);
    setIsFraudToggling(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const result: FraudToggleResponse = await toggleFraudFlag(authId, {
        current_fraud_status: detail.fraud_status,
      });

      // Replaces: COPAUS1C POPULATE-AUTH-DETAILS after MARK-AUTH-FRAUD success
      setDetail((prev) =>
        prev
          ? {
              ...prev,
              fraud_status: result.new_fraud_status,
              fraud_status_display: result.fraud_status_display,
            }
          : prev,
      );

      // Show WS-FRD-ACT-MSG equivalent
      const action =
        result.new_fraud_status === 'F' ? 'Fraud confirmed' : 'Fraud flag removed';
      setSuccessMessage(`${action} — ${result.message}`);

      // Reload fraud logs to show new audit entry
      const updatedLogs = await getFraudLogs(authId);
      setFraudLogs(updatedLogs);
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 409) {
          // FRAUD_STATUS_MISMATCH — stale data, reload
          setErrorMessage(
            'Fraud status was updated by another session. Reloading...',
          );
          await loadDetail();
        } else {
          // WS-FRD-UPDT-FAILED equivalent
          setErrorMessage(
            err.apiError.message || 'Failed to update fraud status. Please try again.',
          );
        }
      } else {
        setErrorMessage('An unexpected error occurred during fraud toggle.');
      }
    } finally {
      setIsFraudToggling(false);
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading authorization details...</div>
      </div>
    );
  }

  if (!detail && !isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="bg-red-50 border border-red-300 rounded-md p-4 mb-4">
            <p className="text-red-700 text-sm font-medium">
              {errorMessage || `Authorization ${authId} not found.`}
            </p>
          </div>
          <Link
            href="/authorizations"
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            Back to Authorizations
          </Link>
        </div>
      </div>
    );
  }

  const fraudConfig = detail
    ? FRAUD_STATUS_CONFIG[detail.fraud_status]
    : null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                View Authorization Details
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                COPAUS1C — Transaction CPVD — Auth #{authId}
              </p>
            </div>
            {/* PF3=Back → XCTL COPAUS0C */}
            <Link
              href="/authorizations"
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              F3 — Back
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Error message — ERRMSG field row 23 RED */}
        {errorMessage && (
          <div className="bg-red-50 border border-red-300 rounded-md p-4">
            <p className="text-red-700 text-sm font-medium">{errorMessage}</p>
          </div>
        )}
        {successMessage && (
          <div className="bg-green-50 border border-green-300 rounded-md p-4">
            <p className="text-green-700 text-sm font-medium">{successMessage}</p>
          </div>
        )}

        {detail && (
          <>
            {/* Fraud status action bar — PF5=Mark/Remove Fraud */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">Fraud Status:</span>
                <FraudStatusBadge status={detail.fraud_status} />
              </div>
              <div className="flex gap-3">
                {/* PF5=Mark/Remove Fraud — triggers confirmation dialog */}
                <button
                  type="button"
                  onClick={() => setShowConfirmDialog(true)}
                  disabled={isFraudToggling}
                  className={`px-4 py-2 text-sm font-medium rounded-md border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                    detail.fraud_status === 'N'
                      ? 'bg-red-600 text-white border-red-600 hover:bg-red-700'
                      : detail.fraud_status === 'F'
                        ? 'bg-yellow-500 text-white border-yellow-500 hover:bg-yellow-600'
                        : 'bg-red-600 text-white border-red-600 hover:bg-red-700'
                  }`}
                >
                  {isFraudToggling ? 'Processing...' : `F5 — ${fraudConfig?.toggleLabel}`}
                </button>
              </div>
            </div>

            {/* Main detail card — all COPAU01 fields */}
            <AuthorizationDetailCard detail={detail} />

            {/* Fraud audit log — DB2 CARDDEMO.AUTHFRDS */}
            {fraudLogs.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                <div className="px-6 py-4 border-b border-gray-100">
                  <h3 className="text-sm font-semibold text-gray-700">
                    Fraud Audit Log
                  </h3>
                  <p className="text-xs text-gray-500 mt-1">
                    DB2 CARDDEMO.AUTHFRDS — immutable audit trail
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">
                          Date
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">
                          Action
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">
                          Amount
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">
                          Merchant
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-100">
                      {fraudLogs.map((log) => (
                        <tr key={log.log_id}>
                          <td className="px-4 py-3 text-sm text-gray-700">
                            {new Date(log.fraud_report_date).toLocaleString()}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                log.fraud_flag === 'F'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}
                            >
                              {log.fraud_flag_display}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-700">
                            {log.auth_amount != null
                              ? formatCurrency(log.auth_amount)
                              : '—'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-700">
                            {log.merchant_name ?? '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

        {/* Navigation legend — COPAU01 row 24 */}
        <div className="text-xs text-yellow-700 bg-yellow-50 border border-yellow-200 rounded px-4 py-2">
          F3=Back &nbsp;|&nbsp; F5=Mark/Remove Fraud &nbsp;|&nbsp; F8=Next Auth (via list)
        </div>
      </div>

      {/* Fraud toggle confirmation dialog — replaces PF5 → COPAUS2C direct action */}
      {showConfirmDialog && detail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Confirm Fraud Flag Change
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Authorization <strong>#{authId}</strong> — Transaction{' '}
              <strong>{detail.transaction_id}</strong>
            </p>
            <div className="bg-gray-50 rounded-md p-4 mb-4">
              <p className="text-sm text-gray-700">
                Current status:{' '}
                <FraudStatusBadge status={detail.fraud_status} />
              </p>
              <p className="text-sm text-gray-700 mt-2">
                New status will be:{' '}
                <strong>
                  {detail.fraud_status === 'F' ? 'REMOVED' : 'FRAUD CONFIRMED'}
                </strong>
              </p>
            </div>
            <p className="text-xs text-gray-500 mb-6">
              This action will be recorded in the fraud audit log (DB2 AUTHFRDS).
            </p>
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => setShowConfirmDialog(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleFraudToggleConfirm()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
