"use client";

/**
 * DeleteUserDialog — confirmation modal for COUSR03C (Delete User).
 *
 * Mirrors COUSR03C two-phase delete:
 *   Phase 1: Show user details as read-only (ASKIP fields: FNAME, LNAME, USRTYPE)
 *   Phase 2: Confirm deletion on "Delete" button (PF5)
 *
 * ASKIP behaviour → read-only display fields in modal (not editable).
 * Cancelling closes modal without action (PF3 Back).
 */
import { useState } from "react";
import { deleteUser, getErrorMessage } from "@/lib/api";
import { userTypeLabel } from "@/lib/utils";
import type { User } from "@/types";

interface DeleteUserDialogProps {
  user: User;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function DeleteUserDialog({
  user,
  onSuccess,
  onCancel,
}: DeleteUserDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleConfirmDelete() {
    setIsDeleting(true);
    setError(null);
    try {
      await deleteUser(user.user_id);
      onSuccess();
    } catch (err) {
      setError(getErrorMessage(err));
      setIsDeleting(false);
    }
  }

  // Read-only field component — mirrors BMS ASKIP attribute
  function ReadOnlyField({ label, value }: { label: string; value: string }) {
    return (
      <div>
        <dt className="text-sm font-medium text-gray-500">{label}</dt>
        <dd className="mt-1 text-sm text-gray-900 font-medium">{value}</dd>
      </div>
    );
  }

  return (
    /* Modal backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-dialog-title"
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
        {/* Header */}
        <div className="flex items-start gap-3 mb-5">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
            <svg
              className="w-5 h-5 text-red-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <div>
            <h2
              id="delete-dialog-title"
              className="text-lg font-semibold text-gray-900"
            >
              Delete User
            </h2>
            <p className="text-sm text-gray-500 mt-0.5">
              This action cannot be undone.
            </p>
          </div>
        </div>

        {/* Read-only user details — mirrors COUSR03C ASKIP display fields */}
        <dl className="grid grid-cols-2 gap-4 bg-gray-50 rounded-lg p-4 mb-5">
          <ReadOnlyField label="User ID" value={user.user_id} />
          <ReadOnlyField label="User Type" value={userTypeLabel(user.user_type)} />
          <ReadOnlyField label="First Name" value={user.first_name} />
          <ReadOnlyField label="Last Name" value={user.last_name} />
        </dl>

        {/* Error message — mirrors COUSR03C ERRMSG row 23 */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Action buttons — mirrors BMS row 24: F5=Delete, F3=Back */}
        <div className="flex gap-3 justify-end">
          <button
            type="button"
            onClick={onCancel}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-300 disabled:opacity-50"
          >
            Cancel (F3)
          </button>
          <button
            type="button"
            onClick={handleConfirmDelete}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDeleting ? "Deleting..." : "Delete (F5)"}
          </button>
        </div>
      </div>
    </div>
  );
}
