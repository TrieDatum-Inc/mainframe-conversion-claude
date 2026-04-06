"use client";

/**
 * /admin/users/[id]/edit — Edit User page.
 *
 * Modernised from COUSR02C (CU02 transaction) and BMS screen COUSR2A.
 *
 * Two-phase behaviour preserved:
 *   Phase 1 (page load): Fetch user → pre-fill form (mirrors ENTER/READ)
 *   Phase 2 (submit):    PUT with changed fields (mirrors PF5/REWRITE)
 *
 * Business rules:
 *   - Password optional (only sent if non-empty — mirrors DRK PASSWD field)
 *   - 400 "No changes detected" shown inline (mirrors "Please modify to update")
 *   - 404 for unknown user shown inline
 */
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getUser, updateUser, getErrorMessage } from "@/lib/api";
import UserForm from "@/components/Users/UserForm";
import type { UpdateUserPayload, User } from "@/types";

export default function EditUserPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const userId = decodeURIComponent(params.id);

  const [user, setUser] = useState<User | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Phase 1 — fetch user on page load (mirrors COUSR02C ENTER/READ)
  useEffect(() => {
    async function loadUser() {
      try {
        const data = await getUser(userId);
        setUser(data);
      } catch (err) {
        setLoadError(getErrorMessage(err));
      } finally {
        setIsLoading(false);
      }
    }
    loadUser();
  }, [userId]);

  // Phase 2 — submit (mirrors COUSR02C PF5/REWRITE)
  async function handleSubmit(values: Record<string, unknown>) {
    setIsSubmitting(true);
    setServerError(null);
    setSuccessMessage(null);
    try {
      const payload: UpdateUserPayload = {
        first_name: values.first_name as string,
        last_name: values.last_name as string,
        user_type: values.user_type as "A" | "U",
        password: (values.password as string) || undefined,
      };
      const updated = await updateUser(userId, payload);
      setUser(updated);
      setSuccessMessage(`User '${updated.user_id}' has been updated successfully.`);
    } catch (err) {
      setServerError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-2xl mx-auto">
          <nav className="flex items-center gap-2 text-sm text-gray-500 mb-1">
            <Link href="/admin/users" className="hover:text-gray-700">
              User Administration
            </Link>
            <span>/</span>
            <span className="text-gray-900 font-medium">
              Edit {userId}
            </span>
          </nav>
          <h1 className="text-xl font-bold text-gray-900">Update User</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Modify user record (COUSR02C — CU02)
          </p>
        </div>
      </header>

      {/* Form */}
      <main className="max-w-2xl mx-auto px-6 py-8">
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          {isLoading && (
            <p className="text-sm text-gray-500">Loading user details...</p>
          )}

          {loadError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {loadError}
            </div>
          )}

          {successMessage && (
            <div className="mb-5 p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
              {successMessage}
            </div>
          )}

          {!isLoading && user && (
            <>
              {/* Show user_id as read-only context (USRIDIN — ASKIP on update screen) */}
              <div className="mb-5 p-3 bg-gray-50 border border-gray-200 rounded">
                <span className="text-xs text-gray-500 uppercase tracking-wide">
                  Editing User ID
                </span>
                <p className="font-mono font-semibold text-gray-900 mt-0.5">
                  {user.user_id}
                </p>
              </div>

              <UserForm
                mode="edit"
                initialValues={user}
                onSubmit={handleSubmit}
                onCancel={() => router.push("/admin/users")}
                isSubmitting={isSubmitting}
                serverError={serverError}
              />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
