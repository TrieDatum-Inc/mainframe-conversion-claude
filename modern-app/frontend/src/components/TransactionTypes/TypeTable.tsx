"use client";

/**
 * TypeTable — paginated, filterable data table for transaction types.
 *
 * Mirrors the COTRTLIC BMS screen:
 *   - 7 rows per page (COTRTLIC default page size)
 *   - Inline description editing (TRTYPD1–7 UNPROT fields)
 *   - Save All button (F10=Save equivalent)
 *   - Row delete action (TRTSEL selector equivalent)
 *   - Filter by type code and description (TRTYPE / TRDESC fields)
 *   - Pagination (F7=Page Up, F8=Page Down equivalent)
 */

import { useEffect, useState, useCallback } from "react";
import type {
  PaginatedTransactionTypes,
  TransactionType,
  InlineSaveRequest,
} from "@/types";

interface TypeTableProps {
  token: string;
  onEdit: (typeCode: string) => void;
  onAdd: () => void;
  refreshTrigger?: number;
}

interface EditState {
  [typeCode: string]: string;
}

const PAGE_SIZE = 7; // Mirrors COTRTLIC: 7 rows per BMS page

export default function TypeTable({
  token,
  onEdit,
  onAdd,
  refreshTrigger = 0,
}: TypeTableProps) {
  const [data, setData] = useState<PaginatedTransactionTypes | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [page, setPage] = useState(1);
  const [typeCodeFilter, setTypeCodeFilter] = useState("");
  const [descFilter, setDescFilter] = useState("");
  const [editState, setEditState] = useState<EditState>({});
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (typeCodeFilter) params.set("type_code", typeCodeFilter);
      if (descFilter) params.set("description", descFilter);
      params.set("page", String(page));
      params.set("page_size", String(PAGE_SIZE));

      const resp = await fetch(`/api/transaction-types?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
      const json: PaginatedTransactionTypes = await resp.json();
      setData(json);
      // Reset edit state to current descriptions
      const initial: EditState = {};
      json.items.forEach((t) => {
        initial[t.type_code] = t.description;
      });
      setEditState(initial);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [token, page, typeCodeFilter, descFilter, refreshTrigger]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleDescChange = (typeCode: string, value: string) => {
    setEditState((prev) => ({ ...prev, [typeCode]: value }));
  };

  /** Save All — mirrors COTRTLIC F10=Save: only sends changed rows */
  const handleSaveAll = async () => {
    if (!data) return;
    const changed = data.items.filter(
      (t) => editState[t.type_code] !== undefined && editState[t.type_code] !== t.description
    );
    if (changed.length === 0) {
      setSuccessMsg("No changes to save");
      setTimeout(() => setSuccessMsg(null), 3000);
      return;
    }

    const trimmedChanges = changed.map((t) => ({
      type_code: t.type_code,
      description: editState[t.type_code].trim(),
    }));

    const invalidRows = trimmedChanges.filter((c) => c.description.length === 0);
    if (invalidRows.length > 0) {
      setError("Description cannot be blank");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const body: InlineSaveRequest = { updates: trimmedChanges };
      const resp = await fetch("/api/transaction-types/inline-save", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });
      if (!resp.ok) throw new Error(`Save failed: ${resp.status}`);
      const result = await resp.json();
      setSuccessMsg(`Saved ${result.saved} record(s)`);
      if (result.errors?.length > 0) {
        setError(result.errors.join("; "));
      }
      setTimeout(() => setSuccessMsg(null), 3000);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (typeCode: string) => {
    setError(null);
    try {
      const resp = await fetch(
        `/api/transaction-types/${encodeURIComponent(typeCode)}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!resp.ok && resp.status !== 204) {
        const err = await resp.json().catch(() => ({ detail: "Delete failed" }));
        throw new Error(err.detail);
      }
      setSuccessMsg(`Deleted type '${typeCode}'`);
      setTimeout(() => setSuccessMsg(null), 3000);
      setDeleteConfirm(null);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
      setDeleteConfirm(null);
    }
  };

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchData();
  };

  const hasUnsavedChanges =
    data !== null &&
    data.items.some(
      (t) =>
        editState[t.type_code] !== undefined &&
        editState[t.type_code] !== t.description
    );

  return (
    <div className="space-y-4">
      {/* Filter bar — mirrors COTRTLIC TRTYPE/TRDESC filter fields */}
      <form
        onSubmit={handleFilterSubmit}
        className="flex flex-wrap gap-3 items-end bg-gray-50 border border-gray-200 rounded-lg p-4"
      >
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Type Code
          </label>
          <input
            type="text"
            value={typeCodeFilter}
            onChange={(e) => setTypeCodeFilter(e.target.value.toUpperCase().slice(0, 2))}
            maxLength={2}
            placeholder="e.g. 01"
            className="w-20 border border-gray-300 rounded px-2 py-1.5 text-sm font-mono uppercase focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Description
          </label>
          <input
            type="text"
            value={descFilter}
            onChange={(e) => setDescFilter(e.target.value)}
            maxLength={50}
            placeholder="Filter by description"
            className="w-64 border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
        >
          Filter
        </button>
        <button
          type="button"
          onClick={() => {
            setTypeCodeFilter("");
            setDescFilter("");
            setPage(1);
          }}
          className="px-4 py-1.5 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300 transition-colors"
        >
          Clear
        </button>
        <div className="ml-auto flex gap-2">
          {/* Add button — F2=Add equivalent */}
          <button
            type="button"
            onClick={onAdd}
            className="px-4 py-1.5 bg-green-600 text-white text-sm font-medium rounded hover:bg-green-700 transition-colors"
          >
            + Add Type
          </button>
          {/* Save All — F10=Save equivalent */}
          <button
            type="button"
            onClick={handleSaveAll}
            disabled={saving || !hasUnsavedChanges}
            className="px-4 py-1.5 bg-amber-500 text-white text-sm font-medium rounded hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? "Saving..." : "Save All"}
          </button>
        </div>
      </form>

      {/* Status messages */}
      {successMsg && (
        <div className="bg-green-50 border border-green-200 text-green-800 rounded px-4 py-2 text-sm">
          {successMsg}
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded px-4 py-2 text-sm">
          {error}
        </div>
      )}

      {/* Data table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-24">
                Type Code
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Description (editable)
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider w-40">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-gray-400">
                  Loading...
                </td>
              </tr>
            ) : data?.items.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-gray-400">
                  No transaction types found
                </td>
              </tr>
            ) : (
              data?.items.map((item) => {
                const isDirty = editState[item.type_code] !== item.description;
                return (
                  <tr
                    key={item.type_code}
                    className={isDirty ? "bg-amber-50" : "hover:bg-gray-50"}
                  >
                    <td className="px-4 py-2 font-mono font-semibold text-gray-800">
                      {item.type_code}
                    </td>
                    <td className="px-4 py-2">
                      {/* Inline-editable description — mirrors TRTYPD UNPROT fields */}
                      <input
                        type="text"
                        value={editState[item.type_code] ?? item.description}
                        onChange={(e) =>
                          handleDescChange(item.type_code, e.target.value)
                        }
                        maxLength={50}
                        className={`w-full border rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 ${
                          isDirty
                            ? "border-amber-400 bg-amber-50"
                            : "border-transparent bg-transparent hover:border-gray-300"
                        }`}
                      />
                    </td>
                    <td className="px-4 py-2 text-right space-x-2">
                      <button
                        onClick={() => onEdit(item.type_code)}
                        className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                      >
                        Detail
                      </button>
                      {deleteConfirm === item.type_code ? (
                        <>
                          <span className="text-red-600 text-xs">Sure?</span>
                          <button
                            onClick={() => handleDelete(item.type_code)}
                            className="text-red-600 hover:text-red-800 text-xs font-medium"
                          >
                            Yes
                          </button>
                          <button
                            onClick={() => setDeleteConfirm(null)}
                            className="text-gray-500 hover:text-gray-700 text-xs font-medium"
                          >
                            No
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => setDeleteConfirm(item.type_code)}
                          className="text-red-500 hover:text-red-700 text-xs font-medium"
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination — F7/F8 equivalents */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            Page {data.page} of {data.pages} ({data.total} total)
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Prev (F7)
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
              disabled={page >= data.pages}
              className="px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next (F8)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
