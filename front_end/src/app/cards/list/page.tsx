"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { listCards, extractErrorMessage } from "@/lib/api";
import { AppHeader } from "@/components/layout/AppHeader";
import { MessageBar } from "@/components/ui/MessageBar";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { formatExpiry } from "@/lib/utils";
import type { CardListItem, CardListResponse } from "@/types";

// COCRDLIC WS-MAX-SCREEN-LINES = 7
const PAGE_SIZE = 7;

/**
 * Card List page — COCRDLIC.
 * Paginated list (7 rows = WS-MAX-SCREEN-LINES).
 * Masked card numbers displayed (PCI-DSS compliant).
 * Filterable by account_id.
 */
function CardListContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuthStore();

  const [accountFilter, setAccountFilter] = useState(
    searchParams.get("account_id") || ""
  );
  const [response, setResponse] = useState<CardListResponse | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  useEffect(() => {
    fetchCards(1);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchCards(page: number) {
    setLoading(true);
    setErrorMsg(null);
    try {
      const params: { page: number; page_size: number; account_id?: number } = {
        page,
        page_size: PAGE_SIZE,
      };
      const aid = accountFilter.trim();
      if (aid) {
        params.account_id = parseInt(aid, 10);
      }
      const data = await listCards(params);
      setResponse(data);
      setCurrentPage(page);
    } catch (err) {
      setErrorMsg(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function handleFilter(e: React.FormEvent) {
    e.preventDefault();
    fetchCards(1);
  }

  return (
    <div className="min-h-screen bg-mainframe-bg">
      <AppHeader
        title="CREDIT CARD LIST"
        subtitle="COCRDLIC - BROWSE CREDIT CARDS"
      />

      <main className="container mx-auto px-4 py-6 max-w-5xl">
        {/* Filter bar */}
        <form onSubmit={handleFilter} className="border border-mainframe-border p-4 mb-4">
          <div className="flex items-center space-x-4">
            <label className="text-mainframe-dim text-xs w-28">FILTER BY ACCT:</label>
            <input
              type="text"
              value={accountFilter}
              onChange={(e) => setAccountFilter(e.target.value)}
              maxLength={11}
              className="px-2 py-1 text-sm w-32"
              placeholder="(ALL)"
            />
            <button
              type="submit"
              className="px-4 py-1 text-sm bg-mainframe-border text-mainframe-text hover:bg-mainframe-panel"
            >
              [ ENTER ]
            </button>
            <button
              type="button"
              onClick={() => { setAccountFilter(""); setTimeout(() => fetchCards(1), 0); }}
              className="px-4 py-1 text-sm text-mainframe-dim hover:text-mainframe-text"
            >
              [ CLEAR ]
            </button>
          </div>
        </form>

        {/* Messages */}
        {errorMsg && (
          <div className="mb-4">
            <MessageBar type="error" message={errorMsg} onDismiss={() => setErrorMsg(null)} />
          </div>
        )}

        {loading && <LoadingSpinner message="LOADING CARDS..." />}

        {response && !loading && (
          <>
            {/* Summary */}
            <div className="text-mainframe-dim text-xs mb-2">
              SHOWING {response.items.length} OF {response.total_count} RECORDS
              {" | "}PAGE {response.page} OF {response.total_pages}
            </div>

            {/* Table */}
            <div className="border border-mainframe-border">
              {/* Header row */}
              <div className="grid grid-cols-6 gap-2 px-3 py-2 bg-mainframe-panel text-mainframe-info text-xs font-bold border-b border-mainframe-border">
                <span>CARD NUMBER</span>
                <span>ACCOUNT</span>
                <span className="col-span-2">EMBOSSED NAME</span>
                <span>EXPIRY</span>
                <span>STATUS</span>
              </div>

              {response.items.length === 0 && (
                <div className="px-3 py-4 text-mainframe-dim text-xs text-center">
                  NO RECORDS FOUND
                </div>
              )}

              {response.items.map((card: CardListItem, idx: number) => (
                <div
                  key={card.card_number}
                  className={`grid grid-cols-6 gap-2 px-3 py-2 text-xs cursor-pointer hover:bg-mainframe-panel transition-colors ${
                    idx % 2 === 0 ? "" : "bg-mainframe-header"
                  }`}
                  onClick={() =>
                    router.push(`/cards/view?card_number=${card.card_number}`)
                  }
                >
                  <span className="text-mainframe-info font-mono">
                    {card.card_number_masked}
                  </span>
                  <span className="text-mainframe-text">{card.account_id}</span>
                  <span className="col-span-2 text-mainframe-text">
                    {card.card_embossed_name}
                  </span>
                  <span className="text-mainframe-text">
                    {formatExpiry(card.expiration_month, card.expiration_year)}
                  </span>
                  <span>
                    <StatusBadge status={card.active_status} />
                  </span>
                </div>
              ))}
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-4 text-xs text-mainframe-dim border-t border-mainframe-border pt-2">
              <button
                onClick={() => router.push("/menu")}
                className="hover:text-mainframe-text"
              >
                PF3=MENU
              </button>
              <div className="flex space-x-4">
                <button
                  onClick={() => fetchCards(currentPage - 1)}
                  disabled={currentPage <= 1}
                  className="hover:text-mainframe-text disabled:opacity-30"
                >
                  PF7=PREV
                </button>
                <span>PAGE {currentPage}/{response.total_pages}</span>
                <button
                  onClick={() => fetchCards(currentPage + 1)}
                  disabled={currentPage >= response.total_pages}
                  className="hover:text-mainframe-text disabled:opacity-30"
                >
                  PF8=NEXT
                </button>
              </div>
              <button
                onClick={() =>
                  router.push(`/accounts/view?account_id=${accountFilter || ""}`)
                }
                className="hover:text-mainframe-text"
              >
                PF5=ACCT VIEW
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default function CardListPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <CardListContent />
    </Suspense>
  );
}
