"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { getAccount, extractErrorMessage } from "@/lib/api";
import { AppHeader } from "@/components/layout/AppHeader";
import { MessageBar } from "@/components/ui/MessageBar";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { CurrencyDisplay } from "@/components/ui/CurrencyDisplay";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { formatDate, formatCurrency } from "@/lib/utils";
import type { AccountDetailResponse } from "@/types";

/**
 * Account View page — COACTVWC.
 * Displays account and linked customer details.
 * SSN is always masked (***-**-XXXX).
 * All fields are read-only (PROT equivalent).
 */
function AccountViewContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuthStore();

  const [accountIdInput, setAccountIdInput] = useState(
    searchParams.get("account_id") || ""
  );
  const [account, setAccount] = useState<AccountDetailResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  // Auto-fetch if account_id was passed as query param
  useEffect(() => {
    const aid = searchParams.get("account_id");
    if (aid) {
      fetchAccount(Number(aid));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchAccount(accountId: number) {
    setErrorMsg(null);
    setAccount(null);
    setLoading(true);
    try {
      const data = await getAccount(accountId);
      setAccount(data);
    } catch (err) {
      setErrorMsg(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const id = parseInt(accountIdInput, 10);
    if (isNaN(id) || id <= 0) {
      setErrorMsg("ACCOUNT ID MUST BE A POSITIVE NUMBER");
      return;
    }
    fetchAccount(id);
  }

  if (!isAuthenticated) {
    return null; // Prevent flash before redirect fires
  }

  return (
    <div className="min-h-screen bg-mainframe-bg">
      <AppHeader
        title="ACCOUNT VIEW"
        subtitle="COACTVWC - VIEW ACCOUNT AND CUSTOMER DETAILS"
      />

      <main className="container mx-auto px-4 py-6 max-w-4xl">
        {/* Search form */}
        <form onSubmit={handleSearch} className="border border-mainframe-border p-4 mb-4">
          <div className="flex items-center space-x-4">
            <label className="text-mainframe-dim text-xs w-24">ACCT NUM:</label>
            <input
              type="text"
              value={accountIdInput}
              onChange={(e) => setAccountIdInput(e.target.value)}
              maxLength={11}
              className="px-2 py-1 text-sm w-32"
              placeholder="___________"
            />
            <button
              type="submit"
              className="px-4 py-1 text-sm bg-mainframe-border text-mainframe-text hover:bg-mainframe-panel"
            >
              [ ENTER ]
            </button>
          </div>
        </form>

        {/* Messages */}
        {errorMsg && (
          <div className="mb-4">
            <MessageBar type="error" message={errorMsg} onDismiss={() => setErrorMsg(null)} />
          </div>
        )}

        {/* Loading */}
        {loading && <LoadingSpinner message="FETCHING ACCOUNT..." />}

        {/* Account Details */}
        {account && !loading && (
          <div className="space-y-4">
            {/* Account Section */}
            <div className="border border-mainframe-border p-4">
              <h2 className="text-mainframe-info text-sm font-bold mb-3 border-b border-mainframe-border pb-2">
                ACCOUNT INFORMATION
              </h2>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <FieldRow label="ACCT ID" value={String(account.account_id)} />
                <FieldRow
                  label="STATUS"
                  value={
                    <StatusBadge
                      status={account.active_status}
                      activeLabel="ACTIVE (Y)"
                      inactiveLabel="INACTIVE (N)"
                    />
                  }
                />
                <FieldRow
                  label="CREDIT LIMIT"
                  value={<CurrencyDisplay amount={account.credit_limit} />}
                />
                <FieldRow
                  label="CASH LIMIT"
                  value={<CurrencyDisplay amount={account.cash_credit_limit} />}
                />
                <FieldRow
                  label="CURRENT BALANCE"
                  value={<CurrencyDisplay amount={account.current_balance} />}
                />
                <FieldRow
                  label="CYCLE CREDIT"
                  value={<CurrencyDisplay amount={account.current_cycle_credit} />}
                />
                <FieldRow
                  label="CYCLE DEBIT"
                  value={<CurrencyDisplay amount={account.current_cycle_debit} />}
                />
                <FieldRow label="GROUP ID" value={account.group_id || "N/A"} />
                <FieldRow label="OPEN DATE" value={formatDate(account.open_date)} />
                <FieldRow label="EXPIRY DATE" value={formatDate(account.expiration_date)} />
              </div>
            </div>

            {/* Customer Section */}
            <div className="border border-mainframe-border p-4">
              <h2 className="text-mainframe-info text-sm font-bold mb-3 border-b border-mainframe-border pb-2">
                CUSTOMER INFORMATION
              </h2>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <FieldRow label="CUST ID" value={String(account.customer.customer_id)} />
                <FieldRow
                  label="NAME"
                  value={`${account.customer.first_name} ${account.customer.middle_name || ""} ${account.customer.last_name}`.trim()}
                />
                <FieldRow label="SSN" value={account.customer.ssn_masked} />
                <FieldRow label="DOB" value={formatDate(account.customer.date_of_birth)} />
                <FieldRow label="ADDRESS" value={account.customer.address || "N/A"} />
                <FieldRow
                  label="CITY/STATE/ZIP"
                  value={`${account.customer.city || ""} ${account.customer.state || ""} ${account.customer.zip_code || ""}`.trim() || "N/A"}
                />
                <FieldRow label="PHONE" value={account.customer.phone_number || "N/A"} />
                <FieldRow label="EMAIL" value={account.customer.email || "N/A"} />
                <FieldRow
                  label="FICO SCORE"
                  value={String(account.customer.fico_credit_score ?? "N/A")}
                />
              </div>
            </div>

            {/* PF Key bar */}
            <div className="flex justify-between text-xs text-mainframe-dim border-t border-mainframe-border pt-2">
              <button
                onClick={() => router.push("/menu")}
                className="hover:text-mainframe-text"
              >
                PF3=MENU
              </button>
              <button
                onClick={() =>
                  router.push(`/accounts/update?account_id=${account.account_id}`)
                }
                className="hover:text-mainframe-text text-mainframe-warn"
              >
                PF5=UPDATE
              </button>
              <button
                onClick={() =>
                  router.push(`/cards/list?account_id=${account.account_id}`)
                }
                className="hover:text-mainframe-text"
              >
                PF6=CARD LIST
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function FieldRow({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex">
      <span className="text-mainframe-dim w-28 shrink-0">{label}:</span>
      <span className="text-mainframe-text">{value}</span>
    </div>
  );
}

export default function AccountViewPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <AccountViewContent />
    </Suspense>
  );
}
