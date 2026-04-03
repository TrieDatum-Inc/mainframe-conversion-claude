"use client";

/**
 * LoginForm component — maps COSGN00 BMS screen (COSGN0A map).
 *
 * BMS screen layout reference:
 *   Row 17: "Type your User ID and Password, then press ENTER:"
 *   Row 19: "User ID     :" [USERID   ] (8 Char)  — FSET,IC,NORM,UNPROT,GREEN
 *   Row 20: "Password    :" [PASSWD   ] (8 Char)  — DRK,FSET,UNPROT,GREEN (password masking)
 *   Row 23: [ERRMSG (78 chars)]                    — ASKIP,BRT,FSET,RED
 *   Row 24: "ENTER=Sign-on  F3=Exit"
 *
 * Business rules implemented:
 *   BR-001: User ID required
 *   BR-002: Password required
 *   BR-003: Both uppercased before sending (done in api.ts login())
 *   BMS DRK attribute on PASSWD → input type="password"
 *   BMS IC attribute on USERID → autoFocus
 *   BMS PIC X(08) → maxLength=8 on both inputs
 */
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/hooks/useAuth";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { PFKeyBar } from "@/components/ui/PFKeyBar";
import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { getErrorMessage } from "@/lib/utils";

// Validation schema — mirrors COBOL field validations (BR-001, BR-002)
const loginSchema = z.object({
  user_id: z
    .string()
    .min(1, "Please enter User ID ...")          // BR-001 message
    .max(8, "User ID must be 8 characters or less"),  // PIC X(08)
  password: z
    .string()
    .min(1, "Please enter Password ...")          // BR-002 message
    .max(8, "Password must be 8 characters or less"), // PIC X(08)
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const router = useRouter();
  const { login, isLoading } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setServerError(null);
    try {
      const redirectTo = await login(data);
      // BR-006: Admin → /admin-menu, Regular → /main-menu
      router.push(redirectTo);
    } catch (err) {
      setServerError(getErrorMessage(err));
    }
  };

  const handleExit = () => {
    // BR-007: PF3 equivalent — show "Thank you" and return to home
    router.push("/");
  };

  // Display first validation error or server error on the ERRMSG field (row 23)
  const displayError =
    errors.user_id?.message ??
    errors.password?.message ??
    serverError;

  return (
    <div className="flex flex-col min-h-screen bg-gray-950 font-mono">
      {/* Screen header — POPULATE-HEADER-INFO equivalent */}
      <ScreenHeader
        transactionId="CC00"
        programName="COSGN00C"
        serverTime={new Date().toISOString()}
      />

      {/* Main screen content — 24x80 BMS layout */}
      <main className="flex-1 flex flex-col items-center justify-start py-4 px-4">
        <div className="w-full max-w-2xl">

          {/* Row 5: Banner text */}
          <div className="text-center text-gray-300 py-2 text-sm">
            This is a Credit Card Demo Application for Mainframe Modernization
          </div>

          {/* Rows 7-15: ASCII art "dollar bill" decorative block */}
          <div className="text-blue-400 text-xs text-center my-4 leading-tight select-none">
            <div>+==========================================+</div>
            <div>|%%%%%%%  NATIONAL RESERVE NOTE  %%%%%%%%%|</div>
            <div>|%(1)  THE UNITED STATES OF KICSLAND  (1)%|</div>
            <div>|%$$              ___          ********$$%|</div>
            <div>|%$    &#123;x&#125;       (o o)                 $%|</div>
            <div>|%$     ******  (  V  )      O N E     $%|</div>
            <div>|%(1)          ---m-m---             (1)%|</div>
            <div>|%%~~~~~~~~~~~ ONE DOLLAR ~~~~~~~~~~~~~%%|</div>
            <div>+==========================================+</div>
          </div>

          {/* Row 17: Instruction text (TURQUOISE / DFHTURQ) */}
          <p className="text-cyan-400 text-center mb-6 text-sm">
            Type your User ID and Password, then press ENTER:
          </p>

          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            {/* Row 19: User ID field (BMS USERID — FSET,IC,NORM,UNPROT,GREEN) */}
            <div className="flex items-center justify-center mb-4 gap-4">
              <label
                htmlFor="user_id"
                className="text-cyan-400 w-40 text-right text-sm"
              >
                User ID     :
              </label>
              <div className="flex items-center gap-2">
                <input
                  id="user_id"
                  type="text"
                  maxLength={8}
                  autoFocus
                  autoComplete="username"
                  className="w-24 bg-gray-800 text-green-400 border border-gray-600 px-2 py-1 font-mono text-sm focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-400 uppercase"
                  placeholder="        "
                  aria-describedby="user_id_hint"
                  {...register("user_id")}
                />
                <span id="user_id_hint" className="text-blue-400 text-sm">
                  (8 Char)
                </span>
              </div>
            </div>

            {/* Row 20: Password field (BMS PASSWD — DRK,FSET,UNPROT,GREEN) */}
            <div className="flex items-center justify-center mb-6 gap-4">
              <label
                htmlFor="password"
                className="text-cyan-400 w-40 text-right text-sm"
              >
                Password    :
              </label>
              <div className="flex items-center gap-2">
                <input
                  id="password"
                  type="password"
                  maxLength={8}
                  autoComplete="current-password"
                  className="w-24 bg-gray-800 text-green-400 border border-gray-600 px-2 py-1 font-mono text-sm focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-400"
                  placeholder="________"
                  {...register("password")}
                />
                <span className="text-blue-400 text-sm">(8 Char)</span>
              </div>
            </div>

            {/* Submit button (ENTER key equivalent) */}
            <div className="flex justify-center mb-4">
              <button
                type="submit"
                disabled={isLoading}
                className="bg-green-700 hover:bg-green-600 disabled:bg-gray-600 text-white px-8 py-2 font-mono text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-green-400"
                aria-label="Sign on (ENTER key)"
              >
                {isLoading ? "Signing on..." : "ENTER (Sign-on)"}
              </button>
            </div>
          </form>

          {/* Row 23: ERRMSG field — ASKIP,BRT,FSET,RED (or GREEN for info) */}
          <div className="mt-4">
            <ErrorMessage message={displayError} messageType="error" />
          </div>
        </div>
      </main>

      {/* Row 24: PF key bar */}
      <PFKeyBar
        keys={[
          { key: "ENTER", label: "Sign-on" },
          { key: "F3", label: "Exit", onClick: handleExit },
        ]}
      />
    </div>
  );
}
