"use client";

/**
 * Transaction View Screen — CT01 / COTRN01C equivalent.
 *
 * BMS Map: COTRN01 / COTRN1A (24x80)
 * Implements:
 *   - TRNIDIN: enter Tran ID field (IC = initial cursor)
 *   - Auto-fetch when navigated from list (CDEMO-CT01-TRN-SELECTED)
 *   - All display fields: TRNID, CARDNUM, TTYPCD, TCATCD, TRNSRC,
 *     TRNAMT, TDESC, TORIGDT, TPROCDT, MID, MNAME, MCITY, MZIP
 *   - F3=Back, F4=Clear, F5=Browse Tran
 *   - Read-only: no update lock (anomaly in COBOL code — not implemented)
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ApiError, getTransaction } from "@/lib/api";
import type { TransactionDetail } from "@/types/transaction";
import { formatAmount, formatTimestamp } from "@/lib/utils";
import ScreenHeader from "@/components/ui/ScreenHeader";
import ErrorMessage from "@/components/ui/ErrorMessage";

interface Props {
  initialTranId: string;
}

export default function TransactionViewScreen({ initialTranId }: Props) {
  const router = useRouter();
  const [tranIdInput, setTranIdInput] = useState(initialTranId);
  const [detail, setDetail] = useState<TransactionDetail | null>(null);
  const [message, setMessage] = useState<{ text: string; type: "error" | "success" } | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchTransaction = async (id: string) => {
    if (!id.trim()) {
      setMessage({ text: "Tran ID can NOT be empty", type: "error" });
      return;
    }
    setLoading(true);
    setMessage(null);
    setDetail(null);
    try {
      const data = await getTransaction(id.trim());
      setDetail(data);
    } catch (err) {
      const msg = err instanceof ApiError
        ? err.status === 404
          ? `Transaction ID NOT found: ${id}`
          : "Unable to lookup Transaction"
        : "Unable to lookup Transaction";
      setMessage({ text: msg, type: "error" });
    } finally {
      setLoading(false);
    }
  };

  // Auto-fetch on mount — mirrors COTRN01C auto-fetch when TRN-SELECTED is populated
  useEffect(() => {
    if (initialTranId) {
      void fetchTransaction(initialTranId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialTranId]);

  const handleClear = () => {
    setTranIdInput("");
    setDetail(null);
    setMessage(null);
  };

  return (
    <div className="screen-container min-h-screen flex flex-col">
      <ScreenHeader tranId="CT01" pgmName="COTRN01C" title="View Transaction" />

      {/* Title + Input area — Rows 4, 6 */}
      <div className="px-4 py-3 border-b border-gray-800">
        <h2 className="text-yellow-300 font-semibold text-sm text-center mb-3">
          View Transaction
        </h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void fetchTransaction(tranIdInput);
          }}
          className="flex items-center gap-3"
        >
          <label className="field-label text-xs whitespace-nowrap">Enter Tran ID:</label>
          <input
            autoFocus
            type="text"
            value={tranIdInput}
            onChange={(e) => setTranIdInput(e.target.value)}
            maxLength={16}
            className="input-field w-44 text-xs"
            aria-label="Transaction ID"
          />
          <button type="submit" className="btn-primary" disabled={loading}>
            ENTER Fetch
          </button>
          <button
            type="button"
            onClick={handleClear}
            className="btn-secondary"
          >
            F4 Clear
          </button>
          <Link href="/transactions" className="btn-secondary">
            F5 Browse
          </Link>
          <Link href="/" className="btn-secondary">
            F3 Back
          </Link>
        </form>
      </div>

      {/* Separator — Row 8 */}
      <div className="px-4 my-2">
        <div className="border-b border-gray-600 border-dashed" />
      </div>

      {/* Transaction detail fields — Rows 10-20 */}
      {loading ? (
        <div className="px-4 text-gray-500 text-xs">Loading...</div>
      ) : detail ? (
        <div className="px-4 space-y-3 text-xs font-mono flex-1">
          {/* Row 10: Transaction ID + Card Number */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="field-label">Transaction ID: </span>
              <span className="field-value">{detail.tran_id}</span>
            </div>
            <div>
              <span className="field-label">Card Number: </span>
              <span className="field-value">{detail.tran_card_num}</span>
            </div>
          </div>

          {/* Row 12: Type CD + Category CD + Source */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <span className="field-label">Type CD: </span>
              <span className="field-value">{detail.tran_type_cd}</span>
            </div>
            <div>
              <span className="field-label">Category CD: </span>
              <span className="field-value">{detail.tran_cat_cd}</span>
            </div>
            <div>
              <span className="field-label">Source: </span>
              <span className="field-value">{detail.tran_source}</span>
            </div>
          </div>

          {/* Row 14: Description */}
          <div>
            <span className="field-label">Description: </span>
            <span className="field-value">{detail.tran_desc}</span>
          </div>

          {/* Row 16: Amount + Orig Date + Proc Date */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <span className="field-label">Amount: </span>
              <span className={`font-mono ${detail.tran_amt < 0 ? "text-red-400" : "text-green-400"}`}>
                {formatAmount(Number(detail.tran_amt))}
              </span>
            </div>
            <div>
              <span className="field-label">Orig Date: </span>
              <span className="field-value">{formatTimestamp(detail.tran_orig_ts)}</span>
            </div>
            <div>
              <span className="field-label">Proc Date: </span>
              <span className="field-value">{formatTimestamp(detail.tran_proc_ts)}</span>
            </div>
          </div>

          {/* Rows 18-20: Merchant info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="field-label">Merchant ID: </span>
              <span className="field-value">{detail.tran_merchant_id}</span>
            </div>
            <div>
              <span className="field-label">Merchant Name: </span>
              <span className="field-value">{detail.tran_merchant_name}</span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="field-label">Merchant City: </span>
              <span className="field-value">{detail.tran_merchant_city}</span>
            </div>
            <div>
              <span className="field-label">Merchant Zip: </span>
              <span className="field-value">{detail.tran_merchant_zip}</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="px-4 flex-1" />
      )}

      {/* Row 23 — ERRMSG */}
      <div className="px-4 pb-2 mt-4">
        <ErrorMessage message={message?.text ?? null} variant={message?.type ?? "error"} />
      </div>

      {/* Row 24 — PF key legend */}
      <div className="px-4 py-1.5 bg-gray-950 border-t border-gray-700 text-xs text-yellow-400 font-mono">
        ENTER=Fetch &nbsp; F3=Back &nbsp; F4=Clear &nbsp; F5=Browse Tran.
      </div>
    </div>
  );
}
