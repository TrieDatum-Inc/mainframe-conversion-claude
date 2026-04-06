import { redirect } from "next/navigation";

/** Root page — redirects to login. Equivalent to COBOL CICS transaction entry point. */
export default function Home() {
  redirect("/login");
}
