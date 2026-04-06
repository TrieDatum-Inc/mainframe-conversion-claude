"use client";

/**
 * TypeForm — modal/inline form for adding or editing a transaction type.
 *
 * Mirrors the COTRTUP BMS screen (COTRTUPC program):
 *   - TRTYPCD field (2 chars, alphanumeric, non-blank) — disabled in edit mode
 *   - TRTYDSC field (max 50 chars, non-blank)
 *   - Add mode: shows type_code + description (COTRTUPC F6=Add)
 *   - Edit mode: shows description only + Delete button (COTRTUPC F4/F5)
 *   - Cancel closes without saving (COTRTUPC F12=Cancel)
 *   - Validation mirrors COBOL field rules
 */

import { useState, useEffect } from "react";
import type { TransactionType } from "@/types";

interface TypeFormProps {
  token: string;
  existing?: TransactionType | null; // null/undefined = add mode
  onSaved: () => void;
  onCancelled: () => void;
}

interface FormErrors {
  type_code?: string;
  description?: string;
  general?: string;
}

const ALPHANUMERIC_RE = /^[A-Za-z0-9]+$/;

function validateTypeCode(value: string): string | undefined {
  if (!value || value.trim().length === 0) return "Type code is required";
  if (value.length !== 2) return "Type code must be exactly 2 characters";
  if (!ALPHANUMERIC_RE.test(value)) return "Type code must be alphanumeric (A-Z, 0-9)";
  return undefined;
}

function validateDescription(value: string): string | undefined {
  if (!value || value.trim().length === 0) return "Description is required";
  if (value.length > 50) return "Description must not exceed 50 characters";
  return undefined;
}

export default function TypeForm({
  token,
  existing,
  onSaved,
  onCancelled,
}: TypeFormProps) {
  const isEditMode = existing !== null && existing !== undefined;

  const [typeCode, setTypeCode] = useState(existing?.type_code ?? "");
  const [description, setDescription] = useState(existing?.description ?? "");
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    setTypeCode(existing?.type_code ?? "");
    setDescription(existing?.description ?? "");
    setErrors({});
    setShowDeleteConfirm(false);
  }, [existing]);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};
    if (!isEditMode) {
      const tcErr = validateTypeCode(typeCode);
      if (tcErr) newErrors.type_code = tcErr;
    }
    const descErr = validateDescription(description);
    if (descErr) newErrors.description = descErr;
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    setErrors({});

    try {
      let resp: Response;
      if (isEditMode) {
        // F5=Save: PUT existing description
        resp = await fetch(
          `/api/transaction-types/${encodeURIComponent(existing.type_code)}`,
          {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ description: description.trim() }),
          }
        );
      } else {
        // F6=Add: POST new type
        resp = await fetch("/api/transaction-types", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            type_code: typeCode.toUpperCase(),
            description: description.trim(),
          }),
        });
      }

      if (!resp.ok) {
        const errBody = await resp.json().catch(() => ({ detail: "Request failed" }));
        if (resp.status === 409) {
          setErrors({ type_code: errBody.detail });
        } else if (resp.status === 422) {
          setErrors({ general: "Validation error — check your input" });
        } else {
          setErrors({ general: errBody.detail });
        }
        return;
      }

      onSaved();
    } catch (err) {
      setErrors({ general: err instanceof Error ? err.message : "Request failed" });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!isEditMode) return;
    setDeleting(true);
    setErrors({});
    try {
      const resp = await fetch(
        `/api/transaction-types/${encodeURIComponent(existing.type_code)}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!resp.ok && resp.status !== 204) {
        const errBody = await resp.json().catch(() => ({ detail: "Delete failed" }));
        setErrors({ general: errBody.detail });
        return;
      }
      onSaved();
    } catch (err) {
      setErrors({ general: err instanceof Error ? err.message : "Delete failed" });
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 max-w-lg">
      {/* Header — mirrors "Maintain Transaction Type" label in COTRTUP */}
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        {isEditMode ? "Edit Transaction Type" : "Add Transaction Type"}
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Type Code — disabled in edit mode (PK, immutable after creation) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Type Code
            <span className="text-red-500 ml-0.5">*</span>
          </label>
          <input
            type="text"
            value={typeCode}
            onChange={(e) => setTypeCode(e.target.value.toUpperCase().slice(0, 2))}
            disabled={isEditMode}
            maxLength={2}
            placeholder="e.g. 08"
            className={`w-24 border rounded px-3 py-2 text-sm font-mono uppercase tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              isEditMode
                ? "bg-gray-100 text-gray-500 cursor-not-allowed border-gray-200"
                : errors.type_code
                ? "border-red-400"
                : "border-gray-300"
            }`}
          />
          {errors.type_code && (
            <p className="text-red-600 text-xs mt-1">{errors.type_code}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">
            2 characters, alphanumeric (A-Z, 0-9)
          </p>
        </div>

        {/* Description — always editable */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
            <span className="text-red-500 ml-0.5">*</span>
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value.slice(0, 50))}
            maxLength={50}
            placeholder="Enter description (max 50 characters)"
            className={`w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.description ? "border-red-400" : "border-gray-300"
            }`}
          />
          <div className="flex justify-between mt-1">
            {errors.description ? (
              <p className="text-red-600 text-xs">{errors.description}</p>
            ) : (
              <span />
            )}
            <span className="text-xs text-gray-400">
              {description.length}/50
            </span>
          </div>
        </div>

        {/* General error */}
        {errors.general && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded px-3 py-2 text-sm">
            {errors.general}
          </div>
        )}

        {/* Delete confirmation prompt — F4=Delete equivalent */}
        {showDeleteConfirm && (
          <div className="bg-red-50 border border-red-200 rounded px-4 py-3 text-sm">
            <p className="text-red-700 font-medium mb-2">
              Delete type &apos;{existing?.type_code}&apos; and all its categories?
              This cannot be undone.
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                className="px-3 py-1.5 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50"
              >
                {deleting ? "Deleting..." : "Yes, Delete"}
              </button>
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(false)}
                className="px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Action buttons — mirrors COTRTUP function key bar */}
        <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100">
          {/* ENTER/F5=Save or F6=Add */}
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {submitting
              ? "Saving..."
              : isEditMode
              ? "Save (F5)"
              : "Add (F6)"}
          </button>

          {/* F4=Delete — edit mode only */}
          {isEditMode && !showDeleteConfirm && (
            <button
              type="button"
              onClick={() => setShowDeleteConfirm(true)}
              className="px-4 py-2 bg-red-100 text-red-700 text-sm font-medium rounded hover:bg-red-200 transition-colors"
            >
              Delete (F4)
            </button>
          )}

          {/* F12=Cancel / F3=Exit */}
          <button
            type="button"
            onClick={onCancelled}
            className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded hover:bg-gray-200 transition-colors"
          >
            Cancel (F12)
          </button>
        </div>
      </form>
    </div>
  );
}
