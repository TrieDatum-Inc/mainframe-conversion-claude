/**
 * Admin Menu page — COADM01C / Transaction CA00 equivalent.
 *
 * COADM01C flow:
 *   First entry → SEND-MENU-SCREEN (display admin menu, 6 options)
 *   Re-entry:
 *     ENTER → PROCESS-ENTER-KEY → validate (1-6) → XCTL to admin sub-program
 *     PF3   → RETURN-TO-SIGNON-SCREEN (logout)
 *     PGMIDERR → "not installed" message in GREEN
 *
 * Only accessible by user_type='A' (enforced by API /menu/admin → 403 for 'U').
 */
import type { Metadata } from "next";
import { AdminMenuClient } from "./AdminMenuClient";

export const metadata: Metadata = {
  title: "Admin Menu — CardDemo (CA00)",
  description: "CardDemo Admin Menu — COADM01C equivalent",
};

export default function AdminMenuPage() {
  return <AdminMenuClient />;
}
