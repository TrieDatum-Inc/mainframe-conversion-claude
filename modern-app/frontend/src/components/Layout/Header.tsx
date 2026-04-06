"use client";

/**
 * Application header component.
 *
 * Replaces the BMS screen header fields present in COMEN01 and COADM01:
 *   TRNNAME  (CM00 / CA00)   -> hidden in web, not user-visible
 *   PGMNAME  (COMEN01C / COADM01C) -> hidden in web
 *   TITLE01  (CardDemo)       -> shown in logo/brand
 *   CURDATE / CURTIME         -> shown as current date/time
 *   User info from COMMAREA   -> shown in user badge
 */

import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";

export function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    // Clear the auth cookie so middleware redirects to /login
    document.cookie = "carddemo_authed=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    router.push("/login");
  }

  const now = new Date();
  const dateStr = now.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const timeStr = now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-40">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 bg-blue-600 rounded-lg">
          <svg
            className="w-5 h-5 text-white"
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
        <div>
          <span className="font-bold text-gray-900 text-sm">CardDemo</span>
          <span className="ml-2 text-xs text-gray-400 hidden sm:inline">
            {user?.user_type === "A" ? "Administrator" : "Credit Card Management"}
          </span>
        </div>
      </div>

      {/* Right section: date/time + user info + logout */}
      <div className="flex items-center gap-4">
        {/* Date/time — mirrors CURDATE/CURTIME BMS fields */}
        <div className="hidden md:flex flex-col items-end text-xs text-gray-400">
          <span>{dateStr}</span>
          <span>{timeStr}</span>
        </div>

        {/* User badge — maps to CDEMO-USER-ID / CDEMO-USER-TYPE */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
            <span className="text-xs font-bold text-blue-700">
              {user?.first_name?.[0] ?? user?.user_id?.[0] ?? "?"}
            </span>
          </div>
          <div className="hidden sm:block">
            <div className="text-xs font-medium text-gray-900">
              {user?.first_name} {user?.last_name}
            </div>
            <div className="text-xs text-gray-400">{user?.user_id}</div>
          </div>
        </div>

        {/* Logout — maps to COSGN00C PF3 action */}
        <button
          onClick={handleLogout}
          className="text-sm text-gray-500 hover:text-red-600 transition-colors flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-red-50"
          aria-label="Sign out"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
            />
          </svg>
          <span className="hidden sm:inline">Sign out</span>
        </button>
      </div>
    </header>
  );
}
