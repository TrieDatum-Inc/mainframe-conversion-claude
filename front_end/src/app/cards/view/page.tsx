"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { getCard, extractErrorMessage } from "@/lib/api";
import { AppHeader } from "@/components/layout/AppHeader";
import { MessageBar } from "@/components/ui/MessageBar";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { formatExpiry } from "@/lib/utils";
import type { CardDetailResponse } from "@/types";

/**
 * Card View page — COCRDSLC.
 * Displays full card details. All fields read-only (PROT).
 * Account ID is PROT — cannot navigate to update from here directly.
 * Provides PF5=UPDATE to navigate to COCRDUPC.
 */
function CardViewContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuthStore();

  const [cardNumberInput, setCardNumberInput] = useState(
    searchParams.get("card_number") || ""
  );
  const [card, setCard] = useState<CardDetailResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  useEffect(() => {
    const cn = searchParams.get("card_number");
    if (cn) fetchCard(cn);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchCard(cardNumber: string) {
    setLoading(true);
    setErrorMsg(null);
    setCard(null);
    try {
      const data = await getCard(cardNumber.trim());
      setCard(data);
    } catch (err) {
      setErrorMsg(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!cardNumberInput.trim()) {
      setErrorMsg("CARD NUMBER IS REQUIRED");
      return;
    }
    fetchCard(cardNumberInput);
  }

  return (
    <div className="min-h-screen bg-mainframe-bg">
      <AppHeader
        title="CREDIT CARD VIEW"
        subtitle="COCRDSLC - VIEW CARD DETAILS"
      />

      <main className="container mx-auto px-4 py-6 max-w-3xl">
        {/* Search */}
        <form onSubmit={handleSearch} className="border border-mainframe-border p-4 mb-4">
          <div className="flex items-center space-x-4">
            <label className="text-mainframe-dim text-xs w-24">CARD NUM:</label>
            <input
              type="text"
              value={cardNumberInput}
              onChange={(e) => setCardNumberInput(e.target.value)}
              maxLength={16}
              className="px-2 py-1 text-sm w-40 font-mono"
              placeholder="________________"
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

        {loading && <LoadingSpinner message="FETCHING CARD..." />}

        {card && !loading && (
          <div className="space-y-4">
            <div className="border border-mainframe-border p-4">
              <h2 className="text-mainframe-info text-sm font-bold mb-4 border-b border-mainframe-border pb-2">
                CARD DETAILS
              </h2>
              <div className="space-y-3 text-xs">
                <FieldRow label="CARD NUMBER" value={card.card_number} mono />
                <FieldRow label="ACCOUNT ID" value={String(card.account_id)} />
                <FieldRow label="EMBOSSED NAME" value={card.card_embossed_name} />
                <FieldRow
                  label="STATUS"
                  value={<StatusBadge status={card.active_status} activeLabel="ACTIVE (Y)" inactiveLabel="INACTIVE (N)" />}
                />
                <FieldRow
                  label="EXPIRY"
                  value={formatExpiry(card.expiration_month, card.expiration_year)}
                />
                {card.expiration_day && (
                  <FieldRow label="EXPIRY DAY" value={String(card.expiration_day)} />
                )}
                <FieldRow label="LAST UPDATED" value={card.updated_at} mono />
              </div>
            </div>

            {/* PF bar */}
            <div className="flex justify-between text-xs text-mainframe-dim border-t border-mainframe-border pt-2">
              <button
                onClick={() => router.push("/cards/list")}
                className="hover:text-mainframe-text"
              >
                PF3=CARD LIST
              </button>
              <button
                onClick={() => router.push("/menu")}
                className="hover:text-mainframe-text"
              >
                PF4=MENU
              </button>
              <button
                onClick={() =>
                  router.push(
                    `/cards/update?card_number=${card.card_number}`
                  )
                }
                className="hover:text-mainframe-text text-mainframe-warn"
              >
                PF5=UPDATE
              </button>
              <button
                onClick={() =>
                  router.push(`/accounts/view?account_id=${card.account_id}`)
                }
                className="hover:text-mainframe-text"
              >
                PF6=ACCT VIEW
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
  mono = false,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="flex">
      <span className="text-mainframe-dim w-32 shrink-0">{label}:</span>
      <span className={`text-mainframe-text ${mono ? "font-mono" : ""}`}>{value}</span>
    </div>
  );
}

export default function CardViewPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <CardViewContent />
    </Suspense>
  );
}
