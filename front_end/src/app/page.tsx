"use client";

/**
 * Root page — redirect to login or appropriate menu based on auth state.
 *
 * COBOL origin: Replaces CICS RETURN TRANSID('CC00') which returned
 * unauthenticated users back to the COSGN00C sign-on transaction.
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export default function RootPage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated && user) {
      // COBOL origin: CDEMO-USRTYP-ADMIN → XCTL COADM01C else COMEN01C
      router.replace(user.userType === "A" ? "/admin/menu" : "/menu");
    } else {
      router.replace("/login");
    }
  }, [isAuthenticated, user, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="text-slate-500 text-sm">Redirecting...</div>
    </div>
  );
}
