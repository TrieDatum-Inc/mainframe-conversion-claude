"use client";

/**
 * CategoryList — displays and manages categories for a single transaction type.
 *
 * Mirrors the category management section of the COTRTUPC detail view.
 * COBOL equivalent: CARDDEMO.TRANSACTION_TYPE_CATEGORY sub-records.
 *
 * Features:
 *   - List all categories for a type
 *   - Inline add form
 *   - Inline edit of descriptions
 *   - Delete per category (with confirmation)
 */

import { useState, useEffect, useCallback } from "react";
import type { TransactionTypeCategory, CreateCategoryRequest } from "@/types";

interface CategoryListProps {
  token: string;
  typeCode: string;
}

const ALPHANUMERIC_RE = /^[A-Za-z0-9]+$/;

function validateCategoryCode(value: string): string | undefined {
  if (!value || value.trim().length === 0) return "Category code is required";
  if (value.length > 4) return "Category code must be 1-4 characters";
  if (!ALPHANUMERIC_RE.test(value)) return "Must be alphanumeric";
  return undefined;
}

function validateDescription(value: string): string | undefined {
  if (!value || value.trim().length === 0) return "Description is required";
  if (value.length > 50) return "Max 50 characters";
  return undefined;
}

export default function CategoryList({ token, typeCode }: CategoryListProps) {
  const [categories, setCategories] = useState<TransactionTypeCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Inline edit states
  const [editDesc, setEditDesc] = useState<Record<string, string>>({});
  const [editErrors, setEditErrors] = useState<Record<string, string>>({});
  const [savingCode, setSavingCode] = useState<string | null>(null);

  // Add form states
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCode, setNewCode] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [addErrors, setAddErrors] = useState<{
    code?: string;
    desc?: string;
    general?: string;
  }>({});
  const [adding, setAdding] = useState(false);

  // Delete state
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const fetchCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(
        `/api/transaction-types/${encodeURIComponent(typeCode)}/categories`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
      const cats: TransactionTypeCategory[] = await resp.json();
      setCategories(cats);
      const descMap: Record<string, string> = {};
      cats.forEach((c) => {
        descMap[c.category_code] = c.description;
      });
      setEditDesc(descMap);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load categories");
    } finally {
      setLoading(false);
    }
  }, [token, typeCode]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  const handleUpdateCategory = async (categoryCode: string) => {
    const desc = editDesc[categoryCode]?.trim();
    const descErr = validateDescription(desc ?? "");
    if (descErr) {
      setEditErrors((prev) => ({ ...prev, [categoryCode]: descErr }));
      return;
    }
    const original = categories.find((c) => c.category_code === categoryCode);
    if (original?.description === desc) return; // no change

    setSavingCode(categoryCode);
    setEditErrors((prev) => ({ ...prev, [categoryCode]: "" }));
    try {
      const resp = await fetch(
        `/api/transaction-types/${encodeURIComponent(typeCode)}/categories/${encodeURIComponent(categoryCode)}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ description: desc }),
        }
      );
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "Update failed" }));
        setEditErrors((prev) => ({ ...prev, [categoryCode]: err.detail }));
        return;
      }
      await fetchCategories();
    } catch (err) {
      setEditErrors((prev) => ({
        ...prev,
        [categoryCode]: err instanceof Error ? err.message : "Update failed",
      }));
    } finally {
      setSavingCode(null);
    }
  };

  const handleDeleteCategory = async (categoryCode: string) => {
    try {
      const resp = await fetch(
        `/api/transaction-types/${encodeURIComponent(typeCode)}/categories/${encodeURIComponent(categoryCode)}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!resp.ok && resp.status !== 204) {
        const err = await resp.json().catch(() => ({ detail: "Delete failed" }));
        setError(err.detail);
        return;
      }
      setDeleteConfirm(null);
      await fetchCategories();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  const handleAddCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    const codeErr = validateCategoryCode(newCode);
    const descErr = validateDescription(newDesc);
    if (codeErr || descErr) {
      setAddErrors({ code: codeErr, desc: descErr });
      return;
    }

    setAdding(true);
    setAddErrors({});
    try {
      const body: CreateCategoryRequest = {
        category_code: newCode.toUpperCase().trim(),
        description: newDesc.trim(),
      };
      const resp = await fetch(
        `/api/transaction-types/${encodeURIComponent(typeCode)}/categories`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(body),
        }
      );
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "Add failed" }));
        if (resp.status === 409) {
          setAddErrors({ code: `Category '${newCode}' already exists` });
        } else {
          setAddErrors({ general: err.detail });
        }
        return;
      }
      setNewCode("");
      setNewDesc("");
      setShowAddForm(false);
      await fetchCategories();
    } catch (err) {
      setAddErrors({ general: err instanceof Error ? err.message : "Add failed" });
    } finally {
      setAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="text-gray-400 text-sm py-4 text-center">
        Loading categories...
      </div>
    );
  }

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-base font-semibold text-gray-700">
          Categories
          <span className="ml-2 text-xs text-gray-400 font-normal">
            ({categories.length})
          </span>
        </h3>
        <button
          onClick={() => setShowAddForm((v) => !v)}
          className="text-sm px-3 py-1 bg-green-50 border border-green-300 text-green-700 rounded hover:bg-green-100 transition-colors"
        >
          {showAddForm ? "Cancel" : "+ Add Category"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded px-3 py-2 text-sm mb-3">
          {error}
        </div>
      )}

      {/* Add Category form */}
      {showAddForm && (
        <form
          onSubmit={handleAddCategory}
          className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4 space-y-3"
        >
          <h4 className="text-sm font-medium text-green-800">New Category</h4>
          <div className="flex flex-wrap gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Code (max 4 chars)
              </label>
              <input
                type="text"
                value={newCode}
                onChange={(e) =>
                  setNewCode(e.target.value.toUpperCase().slice(0, 4))
                }
                maxLength={4}
                placeholder="RETL"
                className={`w-24 border rounded px-2 py-1.5 text-sm font-mono uppercase focus:outline-none focus:ring-2 focus:ring-green-500 ${
                  addErrors.code ? "border-red-400" : "border-gray-300"
                }`}
              />
              {addErrors.code && (
                <p className="text-red-600 text-xs mt-1">{addErrors.code}</p>
              )}
            </div>
            <div className="flex-1 min-w-48">
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Description
              </label>
              <input
                type="text"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value.slice(0, 50))}
                maxLength={50}
                placeholder="Category description"
                className={`w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 ${
                  addErrors.desc ? "border-red-400" : "border-gray-300"
                }`}
              />
              {addErrors.desc && (
                <p className="text-red-600 text-xs mt-1">{addErrors.desc}</p>
              )}
            </div>
          </div>
          {addErrors.general && (
            <p className="text-red-600 text-xs">{addErrors.general}</p>
          )}
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={adding}
              className="px-4 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
            >
              {adding ? "Adding..." : "Add"}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowAddForm(false);
                setNewCode("");
                setNewDesc("");
                setAddErrors({});
              }}
              className="px-4 py-1.5 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Category table */}
      {categories.length === 0 ? (
        <div className="text-gray-400 text-sm text-center py-6 border border-dashed border-gray-200 rounded">
          No categories defined
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase w-24">
                  Code
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase">
                  Description
                </th>
                <th className="px-3 py-2 text-right text-xs font-semibold text-gray-500 uppercase w-32">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {categories.map((cat) => {
                const isDirty =
                  editDesc[cat.category_code] !== cat.description;
                return (
                  <tr
                    key={cat.category_code}
                    className={isDirty ? "bg-amber-50" : "hover:bg-gray-50"}
                  >
                    <td className="px-3 py-2 font-mono text-gray-700">
                      {cat.category_code}
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="text"
                        value={editDesc[cat.category_code] ?? cat.description}
                        onChange={(e) =>
                          setEditDesc((prev) => ({
                            ...prev,
                            [cat.category_code]: e.target.value,
                          }))
                        }
                        maxLength={50}
                        onBlur={() => handleUpdateCategory(cat.category_code)}
                        className={`w-full border rounded px-2 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 ${
                          isDirty
                            ? "border-amber-400"
                            : "border-transparent bg-transparent hover:border-gray-300"
                        }`}
                      />
                      {editErrors[cat.category_code] && (
                        <p className="text-red-600 text-xs mt-0.5">
                          {editErrors[cat.category_code]}
                        </p>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {savingCode === cat.category_code ? (
                        <span className="text-xs text-gray-400">Saving...</span>
                      ) : deleteConfirm === cat.category_code ? (
                        <>
                          <span className="text-red-600 text-xs mr-1">Delete?</span>
                          <button
                            onClick={() =>
                              handleDeleteCategory(cat.category_code)
                            }
                            className="text-red-600 hover:text-red-800 text-xs font-medium mr-1"
                          >
                            Yes
                          </button>
                          <button
                            onClick={() => setDeleteConfirm(null)}
                            className="text-gray-500 hover:text-gray-700 text-xs"
                          >
                            No
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => setDeleteConfirm(cat.category_code)}
                          className="text-red-400 hover:text-red-600 text-xs font-medium"
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
