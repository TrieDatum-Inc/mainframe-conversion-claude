/**
 * Login page — /login
 *
 * Modern card-based login page replacing the COSGN0A BMS terminal screen.
 *
 * The COSGN00 BMS mapset displayed:
 *   - Title: "AWS Mainframe Modernization / CardDemo" (TITLE01/TITLE02)
 *   - USERID field (protected label, unprotected input)
 *   - PASSWD field (DRK/hidden input)
 *   - ERRMSG in red on row 23
 *   - TRNNAME (CC00), PGMNAME (COSGN00C), CURDATE, CURTIME in header
 *
 * This replaces the green-screen aesthetic with a modern, accessible,
 * responsive card layout.
 */

import { LoginForm } from "@/components/Auth/LoginForm";

export const metadata = {
  title: "Sign In — CardDemo",
};

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-950 via-blue-900 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Application header — replaces TITLE01/TITLE02 BMS fields */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4 shadow-lg">
            <svg
              className="w-9 h-9 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
              />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-white">CardDemo</h1>
          <p className="text-blue-200 mt-1 text-sm">Credit Card Management System</p>
        </div>

        {/* Login card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Sign in to your account</h2>
            <p className="text-sm text-gray-500 mt-1">
              Enter your CardDemo User ID and password
            </p>
          </div>

          <LoginForm />

          {/* Demo credentials hint */}
          <div className="mt-6 pt-5 border-t border-gray-100">
            <p className="text-xs text-gray-400 text-center font-medium uppercase tracking-wide mb-2">
              Demo credentials
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
              <div className="bg-gray-50 rounded-lg p-2 text-center">
                <div className="font-medium text-gray-700">Admin</div>
                <div>ADMIN001 / ADMIN001</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-2 text-center">
                <div className="font-medium text-gray-700">User</div>
                <div>USER0001 / USER0001</div>
              </div>
            </div>
          </div>
        </div>

        <p className="text-center text-blue-300 text-xs mt-6">
          AWS Mainframe Modernization Reference — CardDemo
        </p>
      </div>
    </main>
  );
}
