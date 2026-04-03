/**
 * Login page — Server component wrapper for COSGN00 BMS screen equivalent.
 *
 * COSGN00C Transaction CC00:
 *   Initial entry (EIBCALEN=0) → display signon screen
 *   Re-entry with credentials (Enter key) → PROCESS-ENTER-KEY → READ-USER-SEC-FILE
 *   PF3 → SEND-PLAIN-TEXT goodbye → RETURN (ends session)
 *
 * Modern equivalent:
 *   GET /login → display login form
 *   POST /auth/login (via form submit) → authenticate → redirect based on user_type
 *   Logout button → POST /auth/logout → redirect to /login
 */
import type { Metadata } from "next";
import { LoginForm } from "./LoginForm";

export const metadata: Metadata = {
  title: "Sign On — CardDemo (CC00)",
  description: "CardDemo Login — COSGN00C equivalent",
};

export default function LoginPage() {
  return <LoginForm />;
}
