"use client";

/**
 * /admin/users/new — Add User page.
 *
 * Modernised from COUSR01C (CU01 transaction) and BMS screen COUSR1A.
 * Collects FNAME, LNAME, USERID, PASSWD, USRTYPE and POSTs to /api/users.
 *
 * Success: redirects to user list (mirrors COUSR01C "clear fields, show added message").
 * Duplicate key: shows 409 error inline (mirrors VSAM DUPKEY → "User ID already exist").
 */
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createUser, getErrorMessage } from "@/lib/api";
import UserForm from "@/components/Users/UserForm";
import type { CreateUserPayload } from "@/types";

export default function NewUserPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function handleSubmit(values: Record<string, unknown>) {
    setIsSubmitting(true);
    setServerError(null);
    setSuccessMessage(null);
    try {
      const payload = values as CreateUserPayload;
      const created = await createUser(payload);
      // Mirror COUSR01C success: "User XXXX has been added"
      setSuccessMessage(`User '${created.user_id}' has been added successfully.`);
      // Redirect to list after brief pause so user sees the message
      setTimeout(() => router.push("/admin/users"), 1200);
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
            <span className="text-gray-900 font-medium">Add User</span>
          </nav>
          <h1 className="text-xl font-bold text-gray-900">Add User</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Create a new CardDemo user (COUSR01C — CU01)
          </p>
        </div>
      </header>

      {/* Form */}
      <main className="max-w-2xl mx-auto px-6 py-8">
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          {successMessage && (
            <div className="mb-5 p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
              {successMessage}
            </div>
          )}
          <UserForm
            mode="create"
            onSubmit={handleSubmit}
            onCancel={() => router.push("/admin/users")}
            isSubmitting={isSubmitting}
            serverError={serverError}
          />
        </div>
      </main>
    </div>
  );
}
