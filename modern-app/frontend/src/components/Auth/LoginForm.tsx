"use client";

/**
 * LoginForm component.
 *
 * Modernized web equivalent of the COSGN0A BMS screen (COSGN00 mapset).
 *
 * BMS field mapping:
 *   USERID (X(8), unprotected) -> User ID input
 *   PASSWD (X(8), DRK/non-display) -> Password input (type="password")
 *   ERRMSG (78 chars, RED) -> Error alert div
 *   ENTER key -> Submit button
 *   PF3 -> No equivalent (browser back replaces this)
 *
 * Business rules preserved:
 *   - Both fields uppercased before sending (MOVE FUNCTION UPPER-CASE)
 *   - Both fields required (blank check from COSGN00C)
 *   - Max 8 characters each (PIC X(8) field length)
 *   - Error messages match COSGN00C error conditions
 */

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

interface FormState {
  user_id: string;
  password: string;
}

interface FormErrors {
  user_id?: string;
  password?: string;
  general?: string;
}

export function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const userIdRef = useRef<HTMLInputElement>(null);

  const [form, setForm] = useState<FormState>({ user_id: "", password: "" });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Auto-focus the User ID field — mirrors BMS cursor initial position on USERID
  useEffect(() => {
    userIdRef.current?.focus();
  }, []);

  function validateForm(): FormErrors {
    const newErrors: FormErrors = {};

    // Mirror COSGN00C blank-field checks
    if (!form.user_id.trim()) {
      newErrors.user_id = "User ID is required";
    } else if (form.user_id.trim().length > 8) {
      newErrors.user_id = "User ID must be 8 characters or fewer";
    }

    if (!form.password.trim()) {
      newErrors.password = "Password is required";
    } else if (form.password.trim().length > 8) {
      newErrors.password = "Password must be 8 characters or fewer";
    }

    return newErrors;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});

    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    try {
      await login({
        user_id: form.user_id.trim().toUpperCase(),
        password: form.password.trim().toUpperCase(),
      });
      // Set the auth cookie for middleware route protection
      document.cookie = "carddemo_authed=1; path=/; SameSite=Lax";
      router.push("/dashboard");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Authentication failed";
      // Map backend error messages to user-friendly equivalents
      setErrors({ general: mapErrorMessage(message) });
    } finally {
      setIsSubmitting(false);
    }
  }

  function mapErrorMessage(backendMessage: string): string {
    if (backendMessage.includes("Invalid user ID or password")) {
      return "Invalid User ID or Password. Please check your credentials.";
    }
    if (backendMessage.includes("not found")) {
      return "User not found. Please check your User ID.";
    }
    return "Unable to verify your credentials. Please try again.";
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      {/* General error — maps to ERRMSG field (row 23, RED in BMS) */}
      {errors.general && (
        <div
          role="alert"
          className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700"
        >
          {errors.general}
        </div>
      )}

      {/* USERID field — PIC X(8), cursor initial position */}
      <div>
        <label htmlFor="user_id" className="block text-sm font-medium text-gray-700 mb-1">
          User ID
        </label>
        <input
          ref={userIdRef}
          id="user_id"
          type="text"
          autoComplete="username"
          maxLength={8}
          className={`input-field uppercase ${errors.user_id ? "border-red-400 focus:ring-red-500 focus:border-red-500" : ""}`}
          placeholder="e.g. USER0001"
          value={form.user_id}
          onChange={(e) => {
            setForm((prev) => ({ ...prev, user_id: e.target.value.toUpperCase() }));
            if (errors.user_id) setErrors((prev) => ({ ...prev, user_id: undefined }));
          }}
          disabled={isSubmitting}
          aria-describedby={errors.user_id ? "user_id-error" : undefined}
        />
        {errors.user_id && (
          <p id="user_id-error" className="mt-1 text-xs text-red-600">
            {errors.user_id}
          </p>
        )}
      </div>

      {/* PASSWD field — PIC X(8), DRK attribute (non-display) */}
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          maxLength={8}
          className={`input-field ${errors.password ? "border-red-400 focus:ring-red-500 focus:border-red-500" : ""}`}
          placeholder="Enter password"
          value={form.password}
          onChange={(e) => {
            setForm((prev) => ({ ...prev, password: e.target.value }));
            if (errors.password) setErrors((prev) => ({ ...prev, password: undefined }));
          }}
          disabled={isSubmitting}
          aria-describedby={errors.password ? "password-error" : undefined}
        />
        {errors.password && (
          <p id="password-error" className="mt-1 text-xs text-red-600">
            {errors.password}
          </p>
        )}
      </div>

      {/* ENTER key equivalent — primary submit action */}
      <button
        type="submit"
        disabled={isSubmitting}
        className="btn-primary w-full flex items-center justify-center gap-2"
      >
        {isSubmitting ? (
          <>
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Signing in...
          </>
        ) : (
          "Sign In"
        )}
      </button>
    </form>
  );
}
