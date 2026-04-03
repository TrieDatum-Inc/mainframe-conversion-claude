"use client";

/**
 * Transaction List Screen — CT00 / COTRN00C equivalent.
 *
 * BMS Map: COTRN00 / COTRN0A (24x80)
 * Implements:
 *   - Search Tran ID field (TRNIDIN) → start_tran_id query param
 *   - 10-row paginated list (TRNIDnn, TDATEnn, TDESCnn, TAMTnnn)
 *   - Selection field ('S') → navigate to detail view
 *   - ENTER=Continue, F3=Back, F7=Backward, F8=Forward
 *   - SEND-ERASE-FLG: error messages do not clear the list
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ApiError, listTransactions } from "@/lib/api";
import type { PaginationMeta, TransactionListItem } from "@/types/transaction";
import { formatAmount, formatDateMMDDYY, truncateDesc } from "@/lib/utils";
import ScreenHeader from "@/components/ui/ScreenHeader";
import ErrorMessage from "@/components/ui/ErrorMessage";

const PAGE_SIZE = 10;

export default function TransactionListScreen() {
  const router = useRouter();

  const [items, setItems] = useState<TransactionListItem[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [searchId, setSearchId] = useState("");
  const [selectedTranId, setSelectedTranId] = useState<string | null>(null);
  const [message, setMessage] = useState<{ text: string; type: "error" | "success" | "info" } | null>(null);
  const [loading, setLoading] = useState(false);

  // Page state — mirrors CDEMO-CT00-PAGE-NUM in COMMAREA
  const [pageNum, setPageNum] = useState(1);

  // Selection fields for each row — mirrors SEL0001..SEL0010
  const [selections, setSelections] = useState<string[]>(Array(10).fill(""));

  const searchRef = useRef<HTMLInputElement>(null);

  const loadPage = useCallback(async (params: {
    direction?: "forward" | "backward";
    startId?: string;
    anchorId?: string;
    targetPage?: number;
  }) => {
    setLoading(true);
    setMessage(null);
    try {
      const resp = await listTransactions({
        page: params.targetPage ?? pageNum,
        page_size: PAGE_SIZE,
        start_tran_id: params.startId,
        direction: params.direction ?? "forward",
        anchor_tran_id: params.anchorId,
      });
      setItems(resp.items);
      setPagination(resp.pagination);
      setSelections(Array(PAGE_SIZE).fill(""));
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Unable to lookup transactions";
      // Mirror SEND-ERASE-FLG=NO: preserve existing list, only update error message
      setMessage({ text: msg, type: "error" });
    } finally {
      setLoading(false);
    }
  }, [pageNum]);

  useEffect(() => {
    void loadPage({});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ENTER key handler — mirrors PROCESS-ENTER-KEY
  const handleEnter = async (e: React.FormEvent) => {
    e.preventDefault();
    if (searchId && !/^\d+$/.test(searchId.trim())) {
      setMessage({ text: "Tran ID must be Numeric", type: "error" });
      return;
    }
    // Check selection fields — mirrors scanning SEL0001..SEL0010
    const selIdx = selections.findIndex((s) => s.trim() !== "");
    if (selIdx >= 0) {
      const selVal = selections[selIdx].trim().toLowerCase();
      if (selVal !== "s") {
        setMessage({ text: "Invalid selection. Valid value is S", type: "error" });
        return;
      }
      const tranId = items[selIdx]?.tran_id;
      if (tranId) {
        router.push(`/transactions/${tranId}`);
        return;
      }
    }
    // No selection — perform search/refresh
    setPageNum(1);
    await loadPage({ startId: searchId || undefined, targetPage: 1 });
  };

  // PF8 — forward page
  const handleForward = async () => {
    if (!pagination?.has_next_page) {
      setMessage({ text: "You are already at the bottom of the page", type: "info" });
      return;
    }
    const nextPage = pageNum + 1;
    setPageNum(nextPage);
    await loadPage({
      direction: "forward",
      startId: pagination.last_tran_id ?? undefined,
      targetPage: nextPage,
    });
  };

  // PF7 — backward page
  const handleBackward = async () => {
    if (pageNum <= 1) {
      setMessage({ text: "You are already at the top of the page", type: "info" });
      return;
    }
    const prevPage = pageNum - 1;
    setPageNum(prevPage);
    await loadPage({
      direction: "backward",
      anchorId: pagination?.first_tran_id ?? undefined,
      targetPage: prevPage,
    });
  };

  const updateSelection = (idx: number, val: string) => {
    setSelections((prev) => {
      const next = [...prev];
      next[idx] = val;
      return next;
    });
  };

  return (
    <div className="screen-container min-h-screen flex flex-col">
      <ScreenHeader tranId="CT00" pgmName="COTRN00C" title="List Transactions" />

      {/* Title + Search area — Row 4-6 */}
      <div className="px-4 py-3 border-b border-gray-800">
        <div className="flex items-center justify-between mb-3">
          <span className="text-yellow-300 font-semibold text-sm">List Transactions</span>
          <span className="text-teal-400 text-xs">
            Page: <span className="text-blue-300">{pageNum}</span>
          </span>
        </div>

        <form onSubmit={handleEnter} className="flex items-center gap-3">
          <label className="field-label text-xs whitespace-nowrap">
            Search Tran ID:
          </label>
          <input
            ref={searchRef}
            type="text"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
            maxLength={16}
            className="input-field w-40 text-xs"
            placeholder="Enter Tran ID"
            aria-label="Search Transaction ID"
          />
          <button type="submit" className="btn-primary">
            ENTER
          </button>
          <button
            type="button"
            onClick={() => void handleBackward()}
            disabled={loading || pageNum <= 1}
            className="btn-secondary"
          >
            F7 Backward
          </button>
          <button
            type="button"
            onClick={() => void handleForward()}
            disabled={loading || !pagination?.has_next_page}
            className="btn-secondary"
          >
            F8 Forward
          </button>
          <Link href="/" className="btn-secondary">
            F3 Back
          </Link>
          <Link href="/transactions/add" className="btn-secondary">
            Add (CT02)
          </Link>
        </form>
      </div>

      {/* Column headers — Row 8-9 */}
      <div className="px-4 pt-2">
        <div className="grid grid-cols-[2rem_9rem_5rem_1fr_8rem] gap-2 text-gray-400 text-xs font-semibold border-b border-gray-700 pb-1">
          <span>Sel</span>
          <span>Transaction ID</span>
          <span>Date</span>
          <span>Description</span>
          <span className="text-right">Amount</span>
        </div>
        <div className="border-b border-gray-600 mb-1 border-dashed" />
      </div>

      {/* Transaction list rows — Rows 10-19 */}
      <div className="px-4 flex-1">
        {loading ? (
          <div className="text-gray-500 text-xs py-4 text-center">Loading...</div>
        ) : items.length === 0 ? (
          <div className="text-gray-500 text-xs py-4 text-center">No transactions found.</div>
        ) : (
          items.map((tran, idx) => (
            <div
              key={tran.tran_id}
              className="grid grid-cols-[2rem_9rem_5rem_1fr_8rem] gap-2 items-center py-0.5 hover:bg-gray-800 text-xs"
            >
              {/* SEL000n — selection field */}
              <input
                type="text"
                value={selections[idx]}
                onChange={(e) => updateSelection(idx, e.target.value)}
                maxLength={1}
                className="w-6 bg-transparent border-b border-green-700 text-green-400 text-center focus:outline-none focus:border-green-400 uppercase"
                aria-label={`Select row ${idx + 1}`}
              />
              {/* TRNIDnn */}
              <span className="text-blue-300 font-mono">{tran.tran_id}</span>
              {/* TDATEnn */}
              <span className="text-blue-300">{formatDateMMDDYY(tran.tran_orig_ts)}</span>
              {/* TDESCnn */}
              <span className="text-blue-300">{truncateDesc(tran.tran_desc)}</span>
              {/* TAMTnnn */}
              <span
                className={`text-right font-mono ${tran.tran_amt < 0 ? "text-red-400" : "text-green-400"}`}
              >
                {formatAmount(Number(tran.tran_amt))}
              </span>
            </div>
          ))
        )}
      </div>

      {/* Row 21 — instructions */}
      <div className="px-4 py-2 text-xs text-gray-400 border-t border-gray-800">
        Type &apos;S&apos; to View Transaction details from the list
      </div>

      {/* Row 23 — error/status message (ERRMSG) */}
      <div className="px-4 pb-2">
        <ErrorMessage
          message={message?.text ?? null}
          variant={message?.type ?? "error"}
        />
      </div>

      {/* Row 24 — PF key legend */}
      <div className="px-4 py-1.5 bg-gray-950 border-t border-gray-700 text-xs text-yellow-400 font-mono">
        ENTER=Continue &nbsp; F3=Back &nbsp; F7=Backward &nbsp; F8=Forward
      </div>
    </div>
  );
}
