/**
 * /admin/users — User List page.
 *
 * Modernised from COUSR00C (CU00 transaction) and BMS screen COUSR0A.
 * Shows a paginated, searchable table of all users with Edit/Delete actions.
 *
 * Admin route protection: In production, wrap with auth middleware or
 * a server component that checks the JWT/session and redirects non-admins.
 */
import Link from "next/link";
import UserTable from "@/components/Users/UserTable";

export const metadata = {
  title: "User Administration — CardDemo",
};

export default function UsersPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wider font-medium">
              CardDemo Admin
            </p>
            <h1 className="text-xl font-bold text-gray-900">
              User Administration
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Manage system users (COUSR00C — CU00)
            </p>
          </div>

          {/* Add User button — mirrors "02: Add User" option from COADM01C menu */}
          <Link
            href="/admin/users/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Add User
          </Link>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        <UserTable />
      </main>
    </div>
  );
}
