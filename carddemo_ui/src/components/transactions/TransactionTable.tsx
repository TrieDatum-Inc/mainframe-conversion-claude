"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { TransactionListItem, PaginatedResponse } from "@/lib/types";
import DataTable, { type Column } from "@/components/ui/DataTable";
import Pagination from "@/components/ui/Pagination";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AlertMessage from "@/components/ui/AlertMessage";

const PAGE_SIZE = 10;

const columns: Column<TransactionListItem & Record<string, unknown>>[] = [
  { key: "tran_id", header: "Transaction ID" },
  { key: "tran_card_num", header: "Card Number" },
  { key: "tran_type_cd", header: "Type" },
  {
    key: "tran_amt",
    header: "Amount",
    render: (val) =>
      new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
        val as number,
      ),
  },
  { key: "tran_orig_ts", header: "Date" },
];

export default function TransactionTable() {
  const router = useRouter();
  const [data, setData] = useState<PaginatedResponse<TransactionListItem> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchTransactions = useCallback((p: number) => {
    setLoading(true);
    setError("");
    api
      .get<PaginatedResponse<TransactionListItem>>(
        `/api/transactions?page=${p}&page_size=${PAGE_SIZE}`,
      )
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchTransactions(page);
  }, [page, fetchTransactions]);

  if (loading && !data) return <LoadingSpinner />;
  if (error) return <AlertMessage type="error" message={error} />;

  return (
    <div className="space-y-4">
      <DataTable
        columns={columns}
        data={(data?.items ?? []) as (TransactionListItem & Record<string, unknown>)[]}
        onRowClick={(row) => router.push(`/transactions/${row.tran_id}`)}
      />
      {data && (
        <Pagination
          page={data.page}
          pageSize={data.page_size}
          totalCount={data.total_count}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
