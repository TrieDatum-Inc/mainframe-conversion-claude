"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { login, extractErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { MessageBar } from "@/components/ui/MessageBar";

const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

/**
 * Login page.
 * Equivalent to COBOL CICS sign-on transaction CESN / COSGN00C.
 */
export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  async function onSubmit(values: LoginFormValues) {
    setErrorMsg(null);
    setLoading(true);
    try {
      const token = await login(values);
      setAuth(token.access_token, token.username, token.role);
      router.push("/menu");
    } catch (err) {
      setErrorMsg(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-mainframe-bg p-4">
      <div className="w-full max-w-md border border-mainframe-border p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-mainframe-text text-xl font-bold tracking-widest">
            AWS MAINFRAME MODERNIZATION
          </h1>
          <h2 className="text-mainframe-info text-lg mt-1">
            CARDDEMO APPLICATION
          </h2>
          <div className="mt-2 border-t border-mainframe-border" />
        </div>

        {/* Error */}
        {errorMsg && (
          <div className="mb-4">
            <MessageBar type="error" message={errorMsg} onDismiss={() => setErrorMsg(null)} />
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="login-username" className="block text-mainframe-dim text-xs mb-1">
              USERID:
            </label>
            <input
              id="login-username"
              {...register("username")}
              type="text"
              maxLength={8}
              autoComplete="username"
              className="w-full px-2 py-1 text-sm uppercase"
              placeholder="________"
            />
            {errors.username && (
              <p className="text-mainframe-error text-xs mt-1">
                {errors.username.message}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="login-password" className="block text-mainframe-dim text-xs mb-1">
              PASSWORD:
            </label>
            <input
              id="login-password"
              {...register("password")}
              type="password"
              maxLength={8}
              autoComplete="current-password"
              className="w-full px-2 py-1 text-sm"
              placeholder="________"
            />
            {errors.password && (
              <p className="text-mainframe-error text-xs mt-1">
                {errors.password.message}
              </p>
            )}
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-mainframe-border text-mainframe-text py-2 text-sm font-bold hover:bg-mainframe-panel disabled:opacity-50 transition-colors"
            >
              {loading ? "SIGNING ON..." : "[ ENTER ]"}
            </button>
          </div>
        </form>

        <div className="mt-6 text-center text-mainframe-dim text-xs">
          <p>PF3=EXIT</p>
        </div>
      </div>
    </main>
  );
}
