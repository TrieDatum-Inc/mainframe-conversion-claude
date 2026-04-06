"use client";

/**
 * /admin/transaction-types/[typeCode] — Transaction Type Detail Page
 *
 * Modernized equivalent of COTRTUPC (CICS transaction CTTU):
 *   - Shows type code (read-only, PK) + editable description
 *   - Save button (COTRTUPC F5=Save)
 *   - Delete button with confirmation (COTRTUPC F4=Delete)
 *   - Shows and manages associated categories below (TRANSACTION_TYPE_CATEGORY)
 *   - Back to list (COTRTUPC F3=Exit → COTRTLIC)
 *
 * Admin-only — redirects non-admin users to dashboard.
 */

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import TypeForm from "@/components/TransactionTypes/TypeForm";
import CategoryList from "@/components/TransactionTypes/CategoryList";
import type { TransactionTypeDetail } from "@/types";

interface Props {
  params: Promise<{ typeCode: string }>;
}

function useAuth() {
  const [token, setToken] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("carddemo_token");
      const userStr = localStorage.getItem("carddemo_user");
      if (stored && userStr) {
        const user = JSON.parse(userStr);
        setToken(stored);
        setIsAdmin(user?.user_type === "A");
      }
    } catch {
      // SSR guard
    } finally {
      setLoading(false);
    }
  }, []);

  return { token, isAdmin, loading };
}

export default function TransactionTypeDetailPage({ params }: Props) {
  const { typeCode: rawTypeCode } = use(params);
  const typeCode = decodeURIComponent(rawTypeCode).toUpperCase();
  const router = useRouter();
  const { token, isAdmin, loading: authLoading } = useAuth();

  const [typeData, setTypeData] = useState<TransactionTypeDetail | null>(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    if (!authLoading && (!token || !isAdmin)) {
      router.push("/dashboard");
    }
  }, [authLoading, token, isAdmin, router]);

  useEffect(() => {
    if (!token) return;
    fetchType();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, typeCode, refreshTrigger]);

  const fetchType = async () => {
    setDataLoading(true);
    setFetchError(null);
    try {
      const resp = await fetch(
        `/api/transaction-types/${encodeURIComponent(typeCode)}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (resp.status === 404) {
        setFetchError(`Transaction type '${typeCode}' not found`);
        return;
      }
      if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
      const data: TransactionTypeDetail = await resp.json();
      setTypeData(data);
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : "Failed to load type");
    } finally {
      setDataLoading(false);
    }
  };

  const handleSaved = () => {
    // After type update or delete, go back to list
    router.push("/admin/transaction-types");
  };

  if (authLoading || dataLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  if (!token || !isAdmin) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <nav className="text-xs text-gray-400 mb-1">
              <button
                onClick={() => router.push("/dashboard")}
                className="hover:text-gray-600"
              >
                Dashboard
              </button>
              <span className="mx-1">/</span>
              <button
                onClick={() => router.push("/admin/transaction-types")}
                className="hover:text-gray-600"
              >
                Transaction Types
              </button>
              <span className="mx-1">/</span>
              <span className="text-gray-600">{typeCode}</span>
            </nav>
            <h1 className="text-xl font-semibold text-gray-800">
              Transaction Type: {typeCode}
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Edit type and manage categories — migrated from COTRTUPC (CICS CTTU)
            </p>
          </div>
          <button
            onClick={() => router.push("/admin/transaction-types")}
            className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1.5 border border-gray-300 rounded"
          >
            Back to List (F3)
          </button>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-6">
        {fetchError ? (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-5 py-4">
            <p className="font-medium">{fetchError}</p>
            <button
              onClick={() => router.push("/admin/transaction-types")}
              className="mt-2 text-sm text-red-600 underline"
            >
              Return to list
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Edit form for the type — mirrors COTRTUP screen */}
            <TypeForm
              token={token}
              existing={typeData}
              onSaved={handleSaved}
              onCancelled={() => router.push("/admin/transaction-types")}
            />

            {/* Category management section — below the form */}
            {typeData && token && (
              <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
                <CategoryList
                  token={token}
                  typeCode={typeCode}
                  key={refreshTrigger}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
