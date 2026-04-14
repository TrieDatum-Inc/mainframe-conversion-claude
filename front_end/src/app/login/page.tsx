"use client";

/**
 * Login page — /login
 *
 * COBOL origin: COSGN00 BMS mapset / map COSGN0A driven by COSGN00C.
 *
 * BMS fields migrated:
 *   USERID  (UNPROT, IC, GREEN)  → User ID text input with autoFocus
 *   PASSWD  (UNPROT, DRK, GREEN) → Password input (type="password")
 *   ERRMSG  (ASKIP, BRT, RED)    → ErrorMessage component below the form
 *   ENTER key                    → "Sign On" primary submit button
 *   PF3 key                      → "Exit" secondary action
 *
 * SECURITY: This page does NOT distinguish "user not found" from "wrong password"
 * in the UI — both show the same error text, matching the server behaviour.
 *
 * UX decision: The original BMS screen included ASCII art (NATIONAL RESERVE NOTE
 * dollar bill graphic). This decorative element is replaced with a clean,
 * professional card layout appropriate for a financial web application.
 * The CardDemo branding and context are preserved in the header and copy.
 */

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter } from "next/navigation";

import { AppHeader } from "@/components/layout/AppHeader";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";
import { LoginResponse } from "@/types/auth";

// ---------------------------------------------------------------------------
// Zod validation schema
// Maps BMS field constraints: USRIDI max 8 chars, PASSWDI max 8 chars (extended to 72)
// COBOL origin: COSGN00C validates 'IF USERIDI = SPACES' before any lookup.
// ---------------------------------------------------------------------------
const loginSchema = z.object({
  userId: z
    .string()
    .min(1, "User ID is required")
    .max(8, "User ID must be 8 characters or less"),
  password: z
    .string()
    .min(1, "Password is required")
    .max(72, "Password must be 72 characters or less"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [serverError, setServerError] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { userId: "", password: "" },
  });

  /**
   * Submit handler — maps COSGN00C PROCESS-ENTER-KEY (ENTER key action).
   *
   * On success: store JWT, update AuthContext, redirect to appropriate menu.
   * On 401: show uniform error message (no enumeration).
   * On 422: field validation errors shown inline.
   */
  const onSubmit = async (values: LoginFormValues) => {
    setIsLoading(true);
    setServerError("");

    try {
      const response = await api.post<LoginResponse>("/api/v1/auth/login", {
        user_id: values.userId,
        password: values.password,
      });

      // Store token and user identity in AuthContext / localStorage
      login(response);

      // Navigate based on user type — replaces CICS XCTL routing
      // COBOL: SEC-USR-TYPE='A' → COADM01C; else → COMEN01C
      router.push(response.redirect_to);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 401) {
          // SECURITY: Show the same message for both user-not-found and wrong password.
          // COBOL origin: Both NOTFND and password mismatch used identical WS-MESSAGE.
          setServerError("Invalid User ID or Password");
        } else if (error.status === 429) {
          setServerError(
            "Too many login attempts. Please wait a moment and try again."
          );
        } else {
          setServerError("An error occurred. Please try again.");
        }
      } else {
        setServerError("Unable to connect to the server. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Exit handler — maps COSGN00C RETURN-TO-PREV-SCREEN (PF3 key).
   *
   * COBOL: PF3 displayed CCDA-MSG-THANK-YOU then bare EXEC CICS RETURN.
   * Modern: Navigate away from the application (or show exit confirmation).
   */
  const handleExit = () => {
    // In a web context, "exit" closes the tab or navigates to an external page.
    // For this application, we simply redirect back to root (which re-evaluates auth state).
    router.push("/");
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Application header — replaces BMS rows 1-3 */}
      <AppHeader programName="COSGN00C" transactionId="CC00" />

      {/* Main content — centered login card */}
      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          {/* Card container */}
          <div className="bg-white rounded-xl shadow-md border border-slate-200 overflow-hidden">
            {/* Card header */}
            <div className="bg-slate-800 px-8 py-6 text-center">
              <h1 className="text-xl font-bold text-white">
                CardDemo
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                Credit Card Management System
              </p>
              <p className="text-slate-500 text-xs mt-3">
                This is a Credit Card Demo Application for Mainframe Modernization
              </p>
            </div>

            {/* Form area */}
            <div className="px-8 py-8">
              <h2 className="text-lg font-semibold text-slate-800 mb-1">
                Sign in to your account
              </h2>
              <p className="text-sm text-slate-500 mb-6">
                Enter your User ID and Password to continue.
              </p>

              <form
                onSubmit={handleSubmit(onSubmit)}
                noValidate
                aria-label="Sign-on form"
              >
                <div className="space-y-5">
                  {/* User ID field — maps USRIDI (UNPROT, IC, GREEN) */}
                  <div>
                    <label
                      htmlFor="userId"
                      className="block text-sm font-medium text-slate-700 mb-1"
                    >
                      User ID
                      <span className="text-slate-400 font-normal ml-1">
                        (8 characters max)
                      </span>
                    </label>
                    <input
                      id="userId"
                      type="text"
                      autoFocus
                      autoComplete="username"
                      maxLength={8}
                      aria-describedby={
                        errors.userId ? "userId-error" : undefined
                      }
                      aria-invalid={!!errors.userId}
                      className={`w-full px-3 py-2 border rounded-md text-sm font-mono
                        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                        ${
                          errors.userId
                            ? "border-red-400 bg-red-50"
                            : "border-slate-300 bg-white"
                        }`}
                      {...register("userId")}
                    />
                    {errors.userId && (
                      <p
                        id="userId-error"
                        role="alert"
                        className="mt-1 text-xs text-red-600"
                      >
                        {errors.userId.message}
                      </p>
                    )}
                  </div>

                  {/* Password field — maps PASSWDI (UNPROT, DRK, GREEN) */}
                  <div>
                    <label
                      htmlFor="password"
                      className="block text-sm font-medium text-slate-700 mb-1"
                    >
                      Password
                    </label>
                    <input
                      id="password"
                      type="password"
                      autoComplete="current-password"
                      aria-describedby={
                        errors.password ? "password-error" : undefined
                      }
                      aria-invalid={!!errors.password}
                      className={`w-full px-3 py-2 border rounded-md text-sm
                        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                        ${
                          errors.password
                            ? "border-red-400 bg-red-50"
                            : "border-slate-300 bg-white"
                        }`}
                      {...register("password")}
                    />
                    {errors.password && (
                      <p
                        id="password-error"
                        role="alert"
                        className="mt-1 text-xs text-red-600"
                      >
                        {errors.password.message}
                      </p>
                    )}
                  </div>

                  {/* Server-side error message — maps ERRMSG (ASKIP, BRT, RED) */}
                  {serverError && (
                    <ErrorMessage message={serverError} color="red" />
                  )}

                  {/* Submit button — maps ENTER key action */}
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400
                      text-white font-semibold py-2.5 px-4 rounded-md text-sm
                      transition-colors duration-150 focus:outline-none focus:ring-2
                      focus:ring-blue-500 focus:ring-offset-2"
                  >
                    {isLoading ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg
                          className="animate-spin h-4 w-4"
                          viewBox="0 0 24 24"
                          fill="none"
                          aria-hidden="true"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8v8H4z"
                          />
                        </svg>
                        Signing in...
                      </span>
                    ) : (
                      "Sign On"
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Footer action — maps PF3 (Exit) key */}
            <div className="px-8 pb-6 text-center border-t border-slate-100 pt-4">
              <button
                type="button"
                onClick={handleExit}
                className="text-sm text-slate-500 hover:text-slate-700 underline
                  focus:outline-none focus:ring-2 focus:ring-slate-400 rounded"
              >
                Exit
              </button>
            </div>
          </div>

          {/* Keyboard hint — replaces BMS row 24 function-key legend */}
          <p className="text-center text-xs text-slate-400 mt-4">
            Press <kbd className="px-1 py-0.5 bg-slate-200 rounded text-slate-600 font-mono text-xs">Enter</kbd> to sign on
          </p>
        </div>
      </main>
    </div>
  );
}
