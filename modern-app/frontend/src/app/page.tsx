import { redirect } from "next/navigation";

/**
 * Root page — redirect to the admin user list.
 * Mirrors CardDemo sign-on routing: admin users land on COADM01C (admin menu).
 */
export default function RootPage() {
  redirect("/admin/users");
}
