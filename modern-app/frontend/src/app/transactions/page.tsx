"use client";

/**
 * /transactions — Transaction list page (COTRN00C modernization).
 *
 * Features:
 *   - Search by Transaction ID (TRNIDIN field)
 *   - Filter by date range, card number
 *   - Paginated table (10 per page, matching COBOL WS-MAX-TRANS-PER-PAGE)
 *   - Color-coded amounts (green=credit, red=debit)
 *   - Click row to view detail (mirrors 'S' selection)
 */

import { useState, useCallback } from "react";
import { listTransactions } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import { TransactionTable } from "@/components/Transactions/TransactionTable";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import type { TransactionPage } from "@/types";
import Link from "next/link";
import { useEffect } from "react";

export default function TransactionsPage() {
  const [data, setData] = useState<TransactionPage | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [transactionId, setTransactionId] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [page, setPage] = useState(1);

  const fetchData = useCallback(
    async (pageNum: number = 1) => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await listTransactions({
          page: pageNum,
          page_size: 10,
          transaction_id: transactionId || undefined,
          card_number: cardNumber || undefined,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
        });
        setData(result);
        setPage(pageNum);
      } catch (e) {
        setError(getErrorMessage(e));
      } finally {
        setIsLoading(false);
      }
    },
    [transactionId, cardNumber, startDate, endDate]
  );

  useEffect(() => {
    fetchData(1);
  }, []);

  function handleSearch() {
    fetchData(1);
  }

  function handlePageChange(newPage: number) {
    fetchData(newPage);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Transactions</h1>
          <p className="text-sm text-slate-500 mt-1 font-mono">CT00 / COTRN00C</p>
        </div>
        <Link href="/transactions/new">
          <Button variant="primary">Add Transaction</Button>
        </Link>
      </div>

      {/* Search / Filter panel */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <Input
            label="Transaction ID"
            placeholder="Search by ID prefix"
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <Input
            label="Card Number"
            placeholder="4000002000000000"
            value={cardNumber}
            onChange={(e) => setCardNumber(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <Input
            label="From Date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          <Input
            label="To Date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
        <Button onClick={handleSearch} variant="primary" size="sm">
          Search
        </Button>
      </div>

      {error && <Alert variant="error" message={error} />}

      {data && (
        <TransactionTable
          data={data}
          onPageChange={handlePageChange}
          isLoading={isLoading}
        />
      )}
    </div>
  );
}
