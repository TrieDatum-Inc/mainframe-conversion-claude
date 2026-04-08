"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

interface AppHeaderProps {
  readonly title: string;
  readonly subtitle?: string;
}

export function AppHeader({ title, subtitle }: AppHeaderProps) {
  const router = useRouter();
  const { username, clearAuth } = useAuthStore();

  function handleLogout() {
    clearAuth();
    router.push("/login");
  }

  return (
    <header className="bg-mainframe-header border-b border-mainframe-border px-4 py-2">
      {/* Top row: system name + user */}
      <div className="flex items-center justify-between text-xs text-mainframe-dim font-mono mb-1">
        <span>AWS MAINFRAME MODERNIZATION - CARDDEMO</span>
        <span>
          USER: <span className="text-mainframe-info">{username ?? "UNKNOWN"}</span>
          {" "}
          <button
            onClick={handleLogout}
            className="ml-4 text-mainframe-warn underline hover:opacity-75"
          >
            [LOGOFF]
          </button>
        </span>
      </div>

      {/* Main title */}
      <div className="text-center font-mono">
        <h1 className="text-mainframe-text text-lg font-bold tracking-widest">{title}</h1>
        {subtitle && (
          <p className="text-mainframe-dim text-xs mt-0.5">{subtitle}</p>
        )}
      </div>

      {/* Bottom separator */}
      <div className="mt-2 border-t border-mainframe-border" />
    </header>
  );
}
