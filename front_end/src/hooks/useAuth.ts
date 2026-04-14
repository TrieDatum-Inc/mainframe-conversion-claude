"use client";

/**
 * useAuth — convenience hook for consuming AuthContext.
 *
 * Usage in any client component:
 *   const { user, isAuthenticated, login, logout } = useAuth();
 */

import { useContext } from "react";
import { AuthContext } from "@/components/auth/AuthProvider";

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
