"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { TransactionTypeItem, PaginatedResponse, MessageResponse } from "@/lib/types";
import DataTable, { type Column } from "@/components/ui/DataTable";
import Pagination from "@/components/ui/Pagination";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AlertMessage from "@/components/ui/AlertMessage";
import ConfirmDialog from "@/components/ui/ConfirmDialog";

const PAGE_SIZE = 10;

export default function TranTypeTable() {
  const [data, setData] = useState<PaginatedResponse<TransactionTypeItem> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [editItem, setEditItem] = useState<TransactionTypeItem | null>(null);
  const [editDesc, setEditDesc] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const fetchTypes = useCallback((p: number) => {
    setLoading(true);
    setError("");
    api
      .get<PaginatedResponse<TransactionTypeItem>>(
        `/api/transaction-types?page=${p}&page_size=${PAGE_SIZE}`,
      )
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchTypes(page);
  }, [page, fetchTypes]);

  const handleEdit = async () => {
    if (!editItem) return;
    try {
      const res = await api.put<MessageResponse>(`/api/transaction-types/${editItem.tran_type}`, {
        tran_type_desc: editDesc,
      });
      setSuccess(res.message || "Transaction type updated.");
      setEditItem(null);
      fetchTypes(page);
    } catch (err) {
      if (err instanceof Error) setError(err.message);
      setEditItem(null);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      const res = await api.delete<MessageResponse>(`/api/transaction-types/${deleteTarget}`);
      setSuccess(res.message || "Transaction type deleted.");
      setDeleteTarget(null);
      fetchTypes(page);
    } catch (err) {
      if (err instanceof Error) setError(err.message);
      setDeleteTarget(null);
    }
  };

  const columns: Column<TransactionTypeItem & Record<string, unknown>>[] = [
    { key: "tran_type", header: "Type Code" },
    { key: "tran_type_desc", header: "Description" },
    {
      key: "tran_type",
      header: "Actions",
      render: (_val, row) => {
        const item = row as TransactionTypeItem;
        return (
          <div className="flex gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setEditItem(item);
                setEditDesc(item.tran_type_desc);
              }}
              className="text-xs text-brand-600 hover:underline"
            >
              Edit
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setDeleteTarget(item.tran_type);
              }}
              className="text-xs text-red-600 hover:underline"
            >
              Delete
            </button>
          </div>
        );
      },
    },
  ];

  if (loading && !data) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      {error && <AlertMessage type="error" message={error} onDismiss={() => setError("")} />}
      {success && <AlertMessage type="success" message={success} onDismiss={() => setSuccess("")} />}
      <DataTable
        columns={columns}
        data={(data?.items ?? []) as (TransactionTypeItem & Record<string, unknown>)[]}
      />
      {data && (
        <Pagination
          page={data.page}
          pageSize={data.page_size}
          totalCount={data.total_count}
          onPageChange={setPage}
        />
      )}

      {/* Edit Dialog */}
      <ConfirmDialog
        open={!!editItem}
        title={`Edit Type: ${editItem?.tran_type ?? ""}`}
        onConfirm={handleEdit}
        onCancel={() => setEditItem(null)}
        confirmLabel="Save"
      >
        <label className="mb-1 block text-sm font-medium text-gray-700">Description</label>
        <input
          type="text"
          value={editDesc}
          onChange={(e) => setEditDesc(e.target.value)}
          className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </ConfirmDialog>

      {/* Delete Dialog */}
      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Transaction Type"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        confirmLabel="Delete"
      >
        <p>Are you sure you want to delete transaction type <strong>{deleteTarget}</strong>?</p>
      </ConfirmDialog>
    </div>
  );
}
