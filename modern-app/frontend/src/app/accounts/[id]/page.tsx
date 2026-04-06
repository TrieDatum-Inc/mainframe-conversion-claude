"use client";

/**
 * /accounts/[id] — Account detail page.
 *
 * Modernizes COACTVWC (View Account Details):
 *   - READ ACCTDAT by ACCT-ID
 *   - READ CUSTDAT via CXACAIX xref
 *   - BROWSE CARDAIX for associated cards
 *
 * All fields are read-only. Edit button transitions to /accounts/[id]/edit.
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { AccountDetail } from "@/components/Accounts/AccountDetail";
import type { AccountDetail as AccountDetailType } from "@/types";

export default function AccountDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();
  const [account, setAccount] = useState<AccountDetailType | null>(null);
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
      <AccountDetail account={account} />
    </div>
  );
}
