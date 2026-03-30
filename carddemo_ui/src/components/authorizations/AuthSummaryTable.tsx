"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { AuthSummaryItem, PaginatedResponse } from "@/lib/types";
import DataTable, { type Column } from "@/components/ui/DataTable";
import Pagination from "@/components/ui/Pagination";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AlertMessage from "@/components/ui/AlertMessage";
import StatusBadge from "@/components/ui/StatusBadge";

const PAGE_SIZE = 10;

const currency = (val: unknown) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
    val as number,
  );

const columns: Column<AuthSummaryItem & Record<string, unknown>>[] = [
  { key: "pa_acct_id", header: "Account ID" },
  { key: "pa_cust_id", header: "Customer ID" },
  {
    key: "pa_auth_status",
    header: "Auth Status",
    render: (val) => <StatusBadge status={String(val)} />,
  },
  { key: "pa_credit_limit", header: "Credit Limit", render: currency },
  { key: "pa_credit_balance", header: "Credit Balance", render: currency },
  { key: "pa_cash_limit", header: "Cash Limit", render: currency },
  { key: "pa_cash_balance", header: "Cash Balance", render: currency },
  { key: "pa_approved_auth_cnt", header: "Approved #" },
  { key: "pa_declined_auth_cnt", header: "Declined #" },
];

export default function AuthSummaryTable() {
  const router = useRouter();
  const [data, setData] = useState<PaginatedResponse<AuthSummaryItem> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchSummary = useCallback((p: number) => {
    setLoading(true);
    setError("");
    api
      .get<PaginatedResponse<AuthSummaryItem>>(
        `/api/authorizations/summary?page=${p}&page_size=${PAGE_SIZE}`,
      )
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchSummary(page);
  }, [page, fetchSummary]);

  if (loading && !data) return <LoadingSpinner />;
  if (error) return <AlertMessage type="error" message={error} />;

  return (
    <div className="space-y-4">
      <DataTable
        columns={columns}
        data={(data?.items ?? []) as (AuthSummaryItem & Record<string, unknown>)[]}
        onRowClick={(row) => router.push(`/authorizations/${row.pa_acct_id}`)}
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
