"use client";

/**
 * AdminMenuClient — maps COADM01 BMS screen (COADM1A map).
 *
 * BMS screen layout reference:
 *   Row 4:    "Admin Menu" (bright, neutral) — vs "Main Menu" in COMEN01
 *   Rows 6-15: [OPTN001] through [OPTN010] — 40-char option lines (6 active)
 *   Row 20:   "Please select an option :" [OPTION (2 chars, NUM, IC, UNDERLINE)]
 *   Row 23:   [ERRMSG] — ASKIP,BRT,FSET,RED/GREEN
 *   Row 24:   "ENTER=Continue  F3=Exit"
 *
 * Business rules (COADM01C):
 *   BR-001: No COMMAREA → redirect to signon (401/403 handling)
 *   BR-003: Option must be 1-6 (CDEMO-ADMIN-OPT-COUNT = 6)
 *   BR-004: DUMMY options → "not installed" in GREEN (not "coming soon")
 *   BR-005: PGMIDERR handler → "not installed" in GREEN
 *   BR-007: PF3 → RETURN-TO-SIGNON-SCREEN (logout)
 *   BR-009: No per-option user type check (all options are admin-only by access to this page)
 */
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import { getAdminMenu, navigateAdminMenu, logout } from "@/lib/api";
import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { PFKeyBar } from "@/components/ui/PFKeyBar";
import { getErrorMessage } from "@/lib/utils";
import type { MenuResponse, MenuOption, MessageType } from "@/types";

export function AdminMenuClient() {
  const router = useRouter();
  const [menu, setMenu] = useState<MenuResponse | null>(null);
  const [selectedOption, setSelectedOption] = useState<string>("");
  const [message, setMessage] = useState<string | null>(null);
  const [messageType, setMessageType] = useState<MessageType>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isNavigating, setIsNavigating] = useState(false);

  useEffect(() => {
    loadMenu();
  }, []);

  async function loadMenu() {
    setIsLoading(true);
    try {
      const data = await getAdminMenu();
      setMenu(data);
    } catch (err) {
      const status = (err as Record<string, unknown>).status;
      if (status === 401 || status === 403) {
        router.push("/login");
        return;
      }
      setMessage(getErrorMessage(err));
      setMessageType("error");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleNavigate() {
    const optNum = parseInt(selectedOption, 10);
    if (!optNum || optNum < 1 || optNum > 6) {
      // BR-003: COADM01C option range 1-6
      setMessage("Please enter a valid option number...");
      setMessageType("error");
      return;
    }

    setIsNavigating(true);
    setMessage(null);
    try {
      const result = await navigateAdminMenu(optNum);
      router.push(result.route);
    } catch (err) {
      const e = err as Record<string, unknown>;
      const detail = e.detail as Record<string, unknown> | string | undefined;
      if (typeof detail === "object" && detail !== null) {
        // BR-004/BR-005: "not installed" in GREEN (DFHGREEN)
        setMessage(detail.message as string);
        setMessageType((detail.message_type as MessageType) ?? "info");
      } else {
        setMessage(getErrorMessage(err));
        setMessageType("error");
      }
    } finally {
      setIsNavigating(false);
    }
  }

  async function handleLogout() {
    // BR-007: PF3 → RETURN-TO-SIGNON-SCREEN
    try {
      await logout();
    } finally {
      router.push("/login");
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen bg-gray-950 items-center justify-center">
        <span className="text-green-400 font-mono animate-pulse">
          Loading admin menu...
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-950 font-mono">
      <ScreenHeader
        transactionId={menu?.transaction_id ?? "CA00"}
        programName={menu?.program_name ?? "COADM01C"}
        serverTime={menu?.server_time}
      />

      <main className="flex-1 px-4 py-2">
        <div className="max-w-2xl mx-auto">
          {/* Admin badge */}
          <div className="text-xs mb-2 flex items-center gap-2">
            <span className="text-gray-400">
              User: {menu?.user.user_id} ({menu?.user.first_name}{" "}
              {menu?.user.last_name})
            </span>
            <span className="bg-yellow-600 text-yellow-100 px-1 text-xs rounded">
              ADMIN
            </span>
          </div>

          {/* Row 4: Section heading */}
          <h1 className="text-center font-bold text-white text-lg mb-4 tracking-wide">
            {menu?.title ?? "Admin Menu"}
          </h1>

          {/* Rows 6-15: Admin options (OPTN001-OPTN010, 6 active) */}
          <div className="mb-6">
            {menu?.options.map((opt: MenuOption) => (
              <div
                key={opt.option_number}
                className={`py-0.5 text-sm ${
                  opt.is_available ? "text-blue-400" : "text-gray-500"
                }`}
              >
                <span className="w-4 inline-block text-right mr-1">
                  {String(opt.option_number).padStart(2, "0")}.
                </span>
                <span className="ml-2">{opt.name}</span>
                {!opt.is_available && (
                  <span className="text-green-600 text-xs ml-2">
                    (not installed)
                  </span>
                )}
              </div>
            ))}
          </div>

          {/* Row 20: Option input — OPTION field (NUM, IC, UNDERLINE, 2 chars) */}
          <div className="flex items-center gap-3 mb-4">
            <label
              htmlFor="admin_option_input"
              className="text-cyan-400 text-sm font-bold"
            >
              Please select an option :
            </label>
            <input
              id="admin_option_input"
              type="number"
              min={1}
              max={6}
              value={selectedOption}
              onChange={(e) => {
                setSelectedOption(e.target.value);
                setMessage(null);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleNavigate();
              }}
              className="w-16 bg-gray-800 text-white border-b-2 border-white px-2 py-1 text-sm text-right focus:outline-none focus:border-green-400"
              placeholder="  "
              autoFocus
              aria-label="Admin menu option number (1-6)"
            />
            <button
              type="button"
              onClick={handleNavigate}
              disabled={isNavigating}
              className="bg-blue-700 hover:bg-blue-600 disabled:bg-gray-600 text-white px-4 py-1 text-sm transition-colors focus:outline-none focus:ring-1 focus:ring-blue-400"
            >
              {isNavigating ? "..." : "ENTER"}
            </button>
          </div>

          {/* Row 23: ERRMSG field — RED for errors, GREEN for "not installed" */}
          <ErrorMessage message={message} messageType={messageType} />
        </div>
      </main>

      {/* Row 24: PF key bar */}
      <PFKeyBar
        keys={[
          { key: "ENTER", label: "Continue" },
          { key: "F3", label: "Exit (Logout)", onClick: handleLogout },
        ]}
      />
    </div>
  );
}
