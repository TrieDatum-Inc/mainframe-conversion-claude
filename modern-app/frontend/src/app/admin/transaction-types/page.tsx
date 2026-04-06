"use client";

/**
 * /admin/transaction-types — Transaction Type List Page
 *
 * Modernized equivalent of COTRTLIC (CICS transaction CTLI).
 *
 * BMS screen feature mapping:
 *   COTRTLIC TRTYPE filter   -> type code filter input
 *   COTRTLIC TRDESC filter   -> description filter input
 *   COTRTLIC 7 editable rows -> TypeTable with inline description editing
 *   COTRTLIC F2=Add          -> "Add Type" button → TypeForm modal
 *   COTRTLIC F7/F8 paging    -> Prev/Next pagination buttons
 *   COTRTLIC F10=Save        -> "Save All" button (inline edits)
 *   Row selection → COTRTUPC -> "Detail" link → /admin/transaction-types/{code}
 *
 * Admin-only: redirects non-admin users back to dashboard.
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import TypeTable from "@/components/TransactionTypes/TypeTable";
import TypeForm from "@/components/TransactionTypes/TypeForm";
import type { TransactionType } from "@/types";

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
      // localStorage may not be available during SSR
    } finally {
      setLoading(false);
    }
  }, []);

  return { token, isAdmin, loading };
}

export default function TransactionTypesPage() {
  const router = useRouter();
  const { token, isAdmin, loading } = useAuth();

  // Modal state for add/edit
  const [showForm, setShowForm] = useState(false);
  const [editingType, setEditingType] = useState<TransactionType | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    if (!loading && (!token || !isAdmin)) {
      router.push("/dashboard");
    }
  }, [loading, token, isAdmin, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  if (!token || !isAdmin) return null;

  const handleAdd = () => {
    setEditingType(null);
    setShowForm(true);
  };

  const handleEdit = (typeCode: string) => {
    router.push(`/admin/transaction-types/${encodeURIComponent(typeCode)}`);
  };

  const handleFormSaved = () => {
    setShowForm(false);
    setEditingType(null);
    setRefreshTrigger((n) => n + 1);
  };

  const handleFormCancelled = () => {
    setShowForm(false);
    setEditingType(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div>
            <nav className="text-xs text-gray-400 mb-1">
              <button
                onClick={() => router.push("/dashboard")}
                className="hover:text-gray-600"
              >
                Dashboard
              </button>
              <span className="mx-1">/</span>
              <span className="text-gray-600">Transaction Types</span>
            </nav>
            <h1 className="text-xl font-semibold text-gray-800">
              Transaction Type Management
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Admin reference data maintenance — migrated from COTRTLIC (CICS
              CTLI)
            </p>
          </div>
          <button
            onClick={() => router.push("/dashboard")}
            className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1.5 border border-gray-300 rounded"
          >
            Exit (F3)
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-6 space-y-6">
        {/* Add/Edit form panel — shown inline above the table */}
        {showForm && (
          <div className="animate-in fade-in slide-in-from-top-2">
            <TypeForm
              token={token}
              existing={editingType}
              onSaved={handleFormSaved}
              onCancelled={handleFormCancelled}
            />
          </div>
        )}

        {/* Main data table */}
        <TypeTable
          token={token}
          onEdit={handleEdit}
          onAdd={handleAdd}
          refreshTrigger={refreshTrigger}
        />
      </div>
    </div>
  );
}
