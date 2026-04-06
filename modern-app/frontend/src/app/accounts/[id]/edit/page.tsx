"use client";

/**
 * /accounts/[id]/edit — Account edit page.
 *
 * Modernizes COACTUPC (Update Account Details — 4400-line COBOL program):
 *   - All account financial fields editable
 *   - All customer demographic fields editable
 *   - Client validation: phone, SSN, state, zip, FICO
 *   - PF5=Save -> PUT /api/accounts/{id}
 *   - PF12=Cancel -> back to detail view
 *
 * Account ID is always read-only (it is the VSAM key — never rewritten).
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { AccountForm } from "@/components/Accounts/AccountForm";
import type { AccountDetail, AccountUpdateRequest } from "@/types";

export default function AccountEditPage() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();
  const [account, setAccount] = useState<AccountDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !id) return;
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiClient.getAccount(token, id);
        setAccount(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load account");
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [token, id]);

  const handleSave = async (payload: AccountUpdateRequest): Promise<void> => {
    if (!token || !id) throw new Error("Not authenticated");
    await apiClient.updateAccount(token, id, payload);
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="text-sm text-gray-500">Loading account...</div>
      </div>
    );
  }

  if (error || !account) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error || "Account not found"}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <AccountForm account={account} onSave={handleSave} />
    </div>
  );
}
