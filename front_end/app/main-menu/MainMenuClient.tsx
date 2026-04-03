"use client";

/**
 * MainMenuClient — maps COMEN01 BMS screen (COMEN1A map).
 *
 * BMS screen layout reference:
 *   Row 4:    "Main Menu" (bright, neutral)
 *   Rows 6-17: [OPTN001] through [OPTN012] — 40-char option lines, BLUE
 *   Row 20:   "Please select an option :" [OPTION (2 chars, NUM, IC, UNDERLINE)]
 *   Row 23:   [ERRMSG] — ASKIP,BRT,FSET,RED/GREEN
 *   Row 24:   "ENTER=Continue  F3=Exit"
 *
 * Business rules:
 *   BR-001: No COMMAREA → redirect to signon (handled by route guard)
 *   BR-003: Option must be 1-11 (validated before API call)
 *   BR-004: Admin-only options show access denied (returns 403)
 *   BR-005: COPAUS0C marked unavailable (authorization extension)
 *   BR-006: DUMMY options show "coming soon" in GREEN
 *   BR-008: PF3 → logout (RETURN-TO-SIGNON-SCREEN)
 */
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import { getMainMenu, navigateMainMenu, logout } from "@/lib/api";
import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { PFKeyBar } from "@/components/ui/PFKeyBar";
import { getErrorMessage } from "@/lib/utils";
import type { MenuResponse, MenuOption, MessageType } from "@/types";

export function MainMenuClient() {
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
      const data = await getMainMenu();
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
    if (!optNum || optNum < 1 || optNum > 11) {
      setMessage("Please enter a valid option number...");
      setMessageType("error");
      return;
    }

    setIsNavigating(true);
    setMessage(null);
    try {
      const result = await navigateMainMenu(optNum);
      // Navigate to the target route
      router.push(result.route);
    } catch (err) {
      const e = err as Record<string, unknown>;
      const detail = e.detail as Record<string, unknown> | string | undefined;
      if (typeof detail === "object" && detail !== null) {
        setMessage(detail.message as string);
        setMessageType(
          (detail.message_type as MessageType) ?? "error"
        );
      } else {
        setMessage(getErrorMessage(err));
        setMessageType("error");
      }
    } finally {
      setIsNavigating(false);
    }
  }

  async function handleLogout() {
    // BR-008: PF3 → RETURN-TO-SIGNON-SCREEN (logout)
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
          Loading menu...
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-950 font-mono">
      <ScreenHeader
        transactionId={menu?.transaction_id ?? "CM00"}
        programName={menu?.program_name ?? "COMEN01C"}
        serverTime={menu?.server_time}
      />

      <main className="flex-1 px-4 py-2">
        <div className="max-w-2xl mx-auto">
          {/* Row 3: User info */}
          <div className="text-gray-400 text-xs mb-2">
            User: {menu?.user.user_id} ({menu?.user.first_name}{" "}
            {menu?.user.last_name})
          </div>

          {/* Row 4: Section heading — BRT, NEUTRAL */}
          <h1 className="text-center font-bold text-white text-lg mb-4 tracking-wide">
            {menu?.title ?? "Main Menu"}
          </h1>

          {/* Rows 6-17: Menu options (OPTN001-OPTN012) — BLUE, ASKIP */}
          <div className="mb-6">
            {menu?.options.map((opt: MenuOption) => (
              <div
                key={opt.option_number}
                className={`py-0.5 text-sm ${
                  opt.is_available
                    ? "text-blue-400"
                    : "text-gray-500 line-through"
                }`}
              >
                <span className="w-4 inline-block text-right mr-1">
                  {String(opt.option_number).padStart(2, "0")}.
                </span>
                <span className="ml-2">{opt.name}</span>
                {!opt.is_available && opt.availability_message && (
                  <span className="text-green-600 text-xs ml-2">
                    ({opt.availability_message})
                  </span>
                )}
              </div>
            ))}
          </div>

          {/* Row 20: Option input — OPTION field (NUM, IC, UNDERLINE, 2 chars) */}
          <div className="flex items-center gap-3 mb-4">
            <label
              htmlFor="option_input"
              className="text-cyan-400 text-sm font-bold"
            >
              Please select an option :
            </label>
            <input
              id="option_input"
              type="number"
              min={1}
              max={11}
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
              aria-label="Menu option number (1-11)"
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

          {/* Row 23: ERRMSG field */}
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
