/**
 * Root page — redirects to /login (COSGN00C entry point).
 *
 * Equivalent to user typing transaction CC00 at a CICS terminal,
 * which invokes COSGN00C as the application entry point.
 */
import { redirect } from "next/navigation";

export default function Home() {
  redirect("/login");
}
