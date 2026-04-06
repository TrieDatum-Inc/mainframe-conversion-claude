"use client";

/**
 * Authorization Detail Page
 *
 * Displays full authorization detail for a single record.
 * Maps to COPAU01 BMS screen (COPAUS1C).
 *
 * Route: /authorizations/[accountId]/details/[detailId]
 *
 * Features:
 * - All fields from COPAU01 organized in sections
 * - Fraud status highlighted RED when fraud_status='F'
 * - FraudToggle button (F5 equivalent)
 * - Back to list (F3 equivalent)
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getAuthorizationDetail } from "@/lib/api";
import type { AuthorizationDetail } from "@/types";
import { AuthDetail } from "@/components/Authorizations/AuthDetail";

export default function AuthorizationDetailPage() {
  const params = useParams<{ accountId: string; detailId: string }>();
  const [detail, setDetail] = useState<AuthorizationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDetail = async () => {
    if (!params.accountId || !params.detailId) return;

    setLoading(true);
    setError(null);

    try {
      const result = await getAuthorizationDetail(
        params.accountId,
        parseInt(params.detailId, 10)
      );
      setDetail(result);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load authorization detail"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
  }, [params.accountId, params.detailId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-sm text-gray-500">Loading authorization detail...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-red-600 mb-2">{error}</p>
          <a
            href="/authorizations"
            className="text-sm text-blue-600 hover:underline"
          >
            Back to Authorizations
          </a>
        </div>
      </div>
    );
  }

  if (!detail) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header — mirrors COPAU01 rows 1-4 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-2xl mx-auto">
          <p className="text-xs text-gray-400 font-mono">CPVD / COPAUS1C</p>
          <h1 className="text-lg font-semibold text-gray-900">View Authorization Details</h1>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-6">
        <AuthDetail
          accountId={params.accountId}
          detail={detail}
          onFraudToggled={loadDetail}
        />
      </div>
    </div>
  );
}
