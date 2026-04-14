"use client";

/**
 * Account View page — /accounts/view
 *
 * COBOL origin: COACTVWC (Transaction CAVW) / BMS mapset COACTVW (map CACTVWA).
 *
 * BMS fields migrated:
 *   ACCTSID  (UNPROT, IC, MUSTFILL, PICIN=99999999999) → 11-digit numeric input, autoFocus, required
 *   ACSTTUS  (ASKIP)  → Active status badge (green Y / red N)
 *   ADTOPEN  (ASKIP)  → Opened date display field
 *   AEXPDT   (ASKIP)  → Expiry date display field
 *   AREISDT  (ASKIP)  → Reissue date display field
 *   ACRDLIM  (ASKIP, PICOUT=+ZZZ,ZZZ,ZZZ.99) → Formatted signed currency
 *   ACSHLIM  (ASKIP)  → Cash credit limit
 *   ACURBAL  (ASKIP)  → Current balance
 *   ACRCYCR  (ASKIP)  → Cycle credit
 *   ACRCYDB  (ASKIP)  → Cycle debit
 *   AADDGRP  (ASKIP)  → Account group
 *   Customer section (rows 11-20): all ASKIP output fields
 *   ACSTSSN  (ASKIP)  → SSN displayed masked (***-**-XXXX)
 *   ERRMSG   (ASKIP, BRT, RED) → ErrorMessage component
 *   INFOMSG  (PROT)   → Informational message (neutral color)
 *   PF3 key  → "Exit" button (router.back())
 *   ENTER    → "View Account" primary submit
 *
 * UX decision: Clean card-based layout replacing the 80×24 3270 terminal format.
 * Financial amounts use Intl.NumberFormat with sign display instead of +ZZZ,ZZZ,ZZZ.99.
 * SSN is always shown as ***-**-XXXX (last 4 digits) as returned by the API.
 * Navigation to /accounts/update is via an explicit "Update Account" button.
 */

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter } from "next/navigation";

import { AppHeader } from "@/components/layout/AppHeader";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";
import { AccountViewResponse } from "@/types/account";

// ---------------------------------------------------------------------------
// Validation schema
// COBOL origin: COACTVWC 2000-PROCESS-INPUTS — account must be non-zero 11-digit numeric.
// BMS: ACCTSID MUSTFILL + PICIN=99999999999 (hardware enforced on terminal).
// ---------------------------------------------------------------------------
const searchSchema = z.object({
  accountId: z
    .string()
    .min(1, "Account number is required")
    .regex(/^\d{1,11}$/, "Account number must be numeric (up to 11 digits)")
    .refine((v) => parseInt(v, 10) > 0, {
      message: "Account number must be non-zero",
    }),
});

type SearchFormValues = z.infer<typeof searchSchema>;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Format a Decimal string as a signed currency value.
 * COBOL origin: PICOUT='+ZZZ,ZZZ,ZZZ.99' — shows sign, comma-grouped digits, 2 decimal places.
 */
function formatCurrency(value: string | null | undefined): string {
  if (value == null) return "—";
  const num = parseFloat(value);
  if (isNaN(num)) return value;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    signDisplay: "always",
    minimumFractionDigits: 2,
  }).format(num);
}

/** Format an ISO date string for display, or show "—" if null. */
function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return value;
}

/** Render a Y/N active status as a colored badge. */
function ActiveStatusBadge({ status }: { status: string }) {
  const isActive = status === "Y";
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
        isActive
          ? "bg-green-100 text-green-800"
          : "bg-red-100 text-red-700"
      }`}
    >
      {isActive ? "Active" : "Inactive"}
    </span>
  );
}

/** Labeled read-only display row. */
function DisplayField({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
        {label}
      </span>
      <span
        className={`text-sm text-slate-800 ${mono ? "font-mono" : ""}`}
      >
        {value || "—"}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------
export default function AccountViewPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  const [account, setAccount] = useState<AccountViewResponse | null>(null);
  const [viewState, setViewState] = useState<
    "idle" | "loading" | "loaded" | "error"
  >("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [searchedId, setSearchedId] = useState<string>("");

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SearchFormValues>({
    resolver: zodResolver(searchSchema),
    defaultValues: { accountId: "" },
  });

  // Auth guard: redirect to login if no token
  // COBOL origin: EIBCALEN=0 → XCTL COSGN00C
  // Must come AFTER all hooks to comply with React Rules of Hooks.
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null;
  }

  /**
   * Fetch account by ID.
   * COBOL origin: COACTVWC MAIN-PARA (CDEMO-PGM-REENTER path) → 9000-READ-ACCT.
   */
  const onSearch = async (values: SearchFormValues) => {
    setViewState("loading");
    setErrorMessage("");
    setSearchedId(values.accountId);

    try {
      const data = await api.get<AccountViewResponse>(
        `/api/v1/accounts/${values.accountId}`
      );
      setAccount(data);
      setViewState("loaded");
    } catch (error) {
      setViewState("error");
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setErrorMessage(
            `Account ${values.accountId} not found in the system.`
          );
        } else if (error.status === 401 || error.status === 403) {
          router.push("/login");
        } else {
          setErrorMessage(error.message || "Failed to retrieve account.");
        }
      } else {
        setErrorMessage("Unable to connect. Please try again.");
      }
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Application header — replaces BMS rows 1-3 */}
      <AppHeader programName="COACTVWC" transactionId="CAVW" />

      <main className="flex-1 px-4 py-8 max-w-5xl mx-auto w-full">
        {/* Page title */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-800">View Account</h1>
          <p className="text-sm text-slate-500 mt-1">
            Enter an account number to view account and customer details.
          </p>
        </div>

        {/* Search form — maps ACCTSID input field */}
        <form
          onSubmit={handleSubmit(onSearch)}
          noValidate
          aria-label="Account search form"
          className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6"
        >
          <div className="flex flex-col sm:flex-row gap-3 items-start">
            <div className="flex-1">
              <label
                htmlFor="accountId"
                className="block text-sm font-medium text-slate-700 mb-1"
              >
                Account Number
                <span className="text-slate-400 font-normal ml-1">
                  (11 digits)
                </span>
              </label>
              <input
                id="accountId"
                type="text"
                autoFocus
                inputMode="numeric"
                maxLength={11}
                placeholder="00000000000"
                aria-describedby={errors.accountId ? "acct-error" : undefined}
                aria-invalid={!!errors.accountId}
                className={`w-full px-3 py-2 border rounded-md text-sm font-mono
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                  ${
                    errors.accountId
                      ? "border-red-400 bg-red-50"
                      : "border-slate-300 bg-white"
                  }`}
                {...register("accountId")}
              />
              {errors.accountId && (
                <p
                  id="acct-error"
                  role="alert"
                  className="mt-1 text-xs text-red-600"
                >
                  {errors.accountId.message}
                </p>
              )}
            </div>

            <div className="flex gap-2 pt-6">
              {/* Primary action — maps ENTER key */}
              <button
                type="submit"
                disabled={viewState === "loading"}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400
                  text-white text-sm font-semibold rounded-md transition-colors
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                {viewState === "loading" ? "Loading…" : "View Account"}
              </button>

              {/* Exit button — maps PF3 */}
              <button
                type="button"
                onClick={() => router.back()}
                className="px-4 py-2 border border-slate-300 text-slate-600 text-sm
                  font-medium rounded-md hover:bg-slate-50 transition-colors
                  focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2"
              >
                Exit
              </button>
            </div>
          </div>
        </form>

        {/* Error/info message — maps ERRMSG (ASKIP, BRT, RED) and INFOMSG */}
        {viewState === "error" && errorMessage && (
          <div className="mb-4">
            <ErrorMessage message={errorMessage} color="red" />
          </div>
        )}

        {/* Account details — shown after successful lookup */}
        {viewState === "loaded" && account && (
          <div className="space-y-6">
            {/* Header row: account ID + status + navigate to update */}
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-bold text-slate-800 font-mono">
                  Account #{account.account_id}
                </h2>
                <ActiveStatusBadge status={account.active_status} />
              </div>
              {/* Navigation to update — replaces COACTVWC → COACTUPC XCTL */}
              <button
                type="button"
                onClick={() =>
                  router.push(
                    `/accounts/update?accountId=${account.account_id}`
                  )
                }
                className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white
                  text-sm font-semibold rounded-md transition-colors
                  focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-2"
              >
                Update Account
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Account Summary card */}
              <section
                aria-label="Account summary"
                className="bg-white rounded-xl border border-slate-200 shadow-sm p-6"
              >
                <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-4 pb-2 border-b border-slate-100">
                  Account Summary
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <DisplayField
                    label="Account Group"
                    value={account.group_id}
                  />
                  <div />
                  <DisplayField
                    label="Opened"
                    value={formatDate(account.open_date)}
                  />
                  <DisplayField
                    label="Expiry"
                    value={formatDate(account.expiration_date)}
                  />
                  <DisplayField
                    label="Reissue Date"
                    value={formatDate(account.reissue_date)}
                  />
                  <div />
                </div>

                <div className="mt-4 pt-4 border-t border-slate-100 space-y-3">
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Financial Details
                  </h4>
                  {/* ACRDLIM — PICOUT='+ZZZ,ZZZ,ZZZ.99' */}
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">Credit Limit</span>
                    <span className="text-sm font-mono font-medium text-slate-800">
                      {formatCurrency(account.credit_limit)}
                    </span>
                  </div>
                  {/* ACSHLIM */}
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">
                      Cash Credit Limit
                    </span>
                    <span className="text-sm font-mono font-medium text-slate-800">
                      {formatCurrency(account.cash_credit_limit)}
                    </span>
                  </div>
                  {/* ACURBAL */}
                  <div className="flex justify-between items-center border-t border-slate-100 pt-2">
                    <span className="text-sm font-medium text-slate-700">
                      Current Balance
                    </span>
                    <span
                      className={`text-sm font-mono font-bold ${
                        parseFloat(account.current_balance) < 0
                          ? "text-red-600"
                          : "text-slate-800"
                      }`}
                    >
                      {formatCurrency(account.current_balance)}
                    </span>
                  </div>
                  {/* ACRCYCR */}
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">
                      Cycle Credit
                    </span>
                    <span className="text-sm font-mono text-green-700">
                      {formatCurrency(account.curr_cycle_credit)}
                    </span>
                  </div>
                  {/* ACRCYDB */}
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">Cycle Debit</span>
                    <span className="text-sm font-mono text-slate-800">
                      {formatCurrency(account.curr_cycle_debit)}
                    </span>
                  </div>
                </div>
              </section>

              {/* Customer Details card — maps BMS rows 11-20 */}
              <section
                aria-label="Customer details"
                className="bg-white rounded-xl border border-slate-200 shadow-sm p-6"
              >
                <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-4 pb-2 border-b border-slate-100">
                  Customer Details
                </h3>

                {account.customer && (
                  <div className="space-y-4">
                    {/* Identity row */}
                    <div className="grid grid-cols-2 gap-4">
                      <DisplayField
                        label="Customer ID"
                        value={account.customer.customer_id}
                        mono
                      />
                      {/* ACSTSSN — always masked: ***-**-XXXX */}
                      <DisplayField
                        label="SSN"
                        value={account.customer.ssn_masked}
                        mono
                      />
                      <DisplayField
                        label="Date of Birth"
                        value={formatDate(account.customer.date_of_birth)}
                      />
                      <DisplayField
                        label="FICO Score"
                        value={account.customer.fico_score?.toString()}
                        mono
                      />
                    </div>

                    {/* Name */}
                    <div className="pt-3 border-t border-slate-100">
                      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
                        Name
                      </p>
                      <p className="text-sm text-slate-800">
                        {[
                          account.customer.first_name,
                          account.customer.middle_name,
                          account.customer.last_name,
                        ]
                          .filter(Boolean)
                          .join(" ")}
                      </p>
                    </div>

                    {/* Address */}
                    <div className="pt-3 border-t border-slate-100">
                      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
                        Address
                      </p>
                      <address className="text-sm text-slate-800 not-italic space-y-0.5">
                        {account.customer.address_line_1 && (
                          <p>{account.customer.address_line_1}</p>
                        )}
                        {account.customer.address_line_2 && (
                          <p>{account.customer.address_line_2}</p>
                        )}
                        {(account.customer.city ||
                          account.customer.state_code) && (
                          <p>
                            {[
                              account.customer.city,
                              account.customer.state_code,
                              account.customer.zip_code,
                            ]
                              .filter(Boolean)
                              .join(", ")}
                          </p>
                        )}
                        {account.customer.country_code && (
                          <p>{account.customer.country_code}</p>
                        )}
                      </address>
                    </div>

                    {/* Contact */}
                    <div className="grid grid-cols-2 gap-4 pt-3 border-t border-slate-100">
                      <DisplayField
                        label="Phone 1"
                        value={account.customer.phone_1}
                        mono
                      />
                      <DisplayField
                        label="Phone 2"
                        value={account.customer.phone_2}
                        mono
                      />
                      <DisplayField
                        label="Govt ID Ref"
                        value={account.customer.government_id_ref}
                        mono
                      />
                      <DisplayField
                        label="EFT Account"
                        value={account.customer.eft_account_id}
                        mono
                      />
                      <div>
                        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                          Primary Card Holder
                        </span>
                        <div className="mt-1">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                              account.customer.primary_card_holder === "Y"
                                ? "bg-blue-100 text-blue-700"
                                : "bg-slate-100 text-slate-600"
                            }`}
                          >
                            {account.customer.primary_card_holder === "Y"
                              ? "Yes"
                              : "No"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </section>
            </div>
          </div>
        )}
      </main>

      {/* Key legend — replaces BMS row 24 */}
      <footer className="bg-white border-t border-slate-200 py-2 px-4 text-xs text-slate-400 text-center">
        Enter = View Account &nbsp;|&nbsp; Exit = Back to previous screen
      </footer>
    </div>
  );
}
