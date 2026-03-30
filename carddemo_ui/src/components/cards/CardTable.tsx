"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { CardListItem, PaginatedResponse } from "@/lib/types";
import DataTable, { type Column } from "@/components/ui/DataTable";
import Pagination from "@/components/ui/Pagination";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AlertMessage from "@/components/ui/AlertMessage";
import StatusBadge from "@/components/ui/StatusBadge";

const PAGE_SIZE = 10;

const columns: Column<CardListItem & Record<string, unknown>>[] = [
  { key: "card_num", header: "Card Number" },
  { key: "card_acct_id", header: "Account ID" },
  {
    key: "card_active_status",
    header: "Status",
    render: (val) => <StatusBadge status={val === "Y" ? "Active" : "Inactive"} />,
  },
  { key: "card_expiration_date", header: "Expiration Date" },
];

export default function CardTable() {
  const router = useRouter();
  const [data, setData] = useState<PaginatedResponse<CardListItem> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchCards = useCallback((p: number) => {
    setLoading(true);
    setError("");
    api
      .get<PaginatedResponse<CardListItem>>(`/api/cards?page=${p}&page_size=${PAGE_SIZE}`)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchCards(page);
  }, [page, fetchCards]);

  if (loading && !data) return <LoadingSpinner />;
  if (error) return <AlertMessage type="error" message={error} />;

  return (
    <div className="space-y-4">
      <DataTable
        columns={columns}
        data={(data?.items ?? []) as (CardListItem & Record<string, unknown>)[]}
        onRowClick={(row) => router.push(`/cards/${row.card_num}`)}
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
