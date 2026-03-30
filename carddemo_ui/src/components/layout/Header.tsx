"use client";

import { useAuth } from "@/context/AuthContext";

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="flex h-14 items-center justify-between bg-brand-900 px-6 text-white">
      <h1 className="text-lg font-semibold tracking-wide">CardDemo</h1>

      {user && (
        <div className="flex items-center gap-4">
          <span className="text-sm text-brand-200">
            Logged in as{" "}
            <span className="font-medium text-white">{user.user_id}</span>{" "}
            ({user.user_type === "A" ? "Admin" : "User"})
          </span>

          <button
            onClick={logout}
            className="rounded-md border border-brand-700 bg-brand-800 px-3 py-1 text-sm font-medium text-brand-100 transition-colors hover:bg-brand-700 hover:text-white"
          >
            Logout
          </button>
        </div>
      )}
    </header>
  );
}
