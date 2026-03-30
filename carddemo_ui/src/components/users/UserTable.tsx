"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { UserListItem, PaginatedResponse, MessageResponse } from "@/lib/types";
import DataTable, { type Column } from "@/components/ui/DataTable";
import Pagination from "@/components/ui/Pagination";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AlertMessage from "@/components/ui/AlertMessage";
import ConfirmDialog from "@/components/ui/ConfirmDialog";

const PAGE_SIZE = 10;

export default function UserTable() {
  const router = useRouter();
  const [data, setData] = useState<PaginatedResponse<UserListItem> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const fetchUsers = useCallback((p: number) => {
    setLoading(true);
    setError("");
    api
      .get<PaginatedResponse<UserListItem>>(`/api/users?page=${p}&page_size=${PAGE_SIZE}`)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchUsers(page);
  }, [page, fetchUsers]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      const res = await api.delete<MessageResponse>(`/api/users/${deleteTarget}`);
      setSuccess(res.message || "User deleted successfully.");
      setDeleteTarget(null);
      fetchUsers(page);
    } catch (err) {
      if (err instanceof Error) setError(err.message);
      setDeleteTarget(null);
    }
  };

  const columns: Column<UserListItem & Record<string, unknown>>[] = [
    { key: "usr_id", header: "User ID" },
    { key: "usr_fname", header: "First Name" },
    { key: "usr_lname", header: "Last Name" },
    { key: "usr_type", header: "Type", render: (val) => (val === "A" ? "Admin" : "Regular") },
    {
      key: "usr_id",
      header: "Actions",
      render: (_val, row) => (
        <div className="flex gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              router.push(`/admin/users/${(row as UserListItem).usr_id}/edit`);
            }}
            className="text-xs text-brand-600 hover:underline"
          >
            Edit
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setDeleteTarget((row as UserListItem).usr_id);
            }}
            className="text-xs text-red-600 hover:underline"
          >
            Delete
          </button>
        </div>
      ),
    },
  ];

  if (loading && !data) return <LoadingSpinner />;
  if (error) return <AlertMessage type="error" message={error} />;

  return (
    <div className="space-y-4">
      {success && <AlertMessage type="success" message={success} onDismiss={() => setSuccess("")} />}
      <DataTable
        columns={columns}
        data={(data?.items ?? []) as (UserListItem & Record<string, unknown>)[]}
      />
      {data && (
        <Pagination
          page={data.page}
          pageSize={data.page_size}
          totalCount={data.total_count}
          onPageChange={setPage}
        />
      )}
      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete User"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        confirmLabel="Delete"
      >
        <p>Are you sure you want to delete user <strong>{deleteTarget}</strong>? This action cannot be undone.</p>
      </ConfirmDialog>
    </div>
  );
}
