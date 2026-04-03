/**
 * Main Menu page — COMEN01C / Transaction CM00 equivalent.
 *
 * COMEN01C flow:
 *   First entry (context=0) → SEND-MENU-SCREEN (display menu)
 *   Re-entry (context=1):
 *     ENTER → PROCESS-ENTER-KEY → validate option → XCTL to sub-program
 *     PF3   → RETURN-TO-SIGNON-SCREEN (logout)
 *     Other → invalid key message → re-send menu
 *
 * BR-001: No COMMAREA (unauthenticated) → handled by useAuth / getMainMenu 401 response
 * BR-004: Admin-only option → 403 from API
 */
import type { Metadata } from "next";
import { MainMenuClient } from "./MainMenuClient";

export const metadata: Metadata = {
  title: "Main Menu — CardDemo (CM00)",
  description: "CardDemo Main Menu — COMEN01C equivalent",
};

export default function MainMenuPage() {
  return <MainMenuClient />;
}
