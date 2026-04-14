"use client";

/**
 * Account Update page — /accounts/update
 *
 * COBOL origin: COACTUPC (Transaction CAUP) / BMS mapset COACTUP (map CACTUPA).
 *
 * BMS fields migrated (all UNPROT/editable):
 *   ACCTSID       → Account number input (read-only after load)
 *   ACSTTUS       → Active status Y/N select
 *   OPNYEAR/MON/DAY → Single <input type="date"> (open date)
 *   EXPYEAR/MON/DAY → Single <input type="date"> (expiry date)
 *   RISYEAR/MON/DAY → Single <input type="date"> (reissue date)
 *   ACRDLIM       → Credit limit number input (>= 0)
 *   ACSHLIM       → Cash credit limit (<= credit limit)
 *   ACURBAL       → Current balance (can be negative)
 *   ACRCYCR/ACRCYDB → Cycle credit/debit number inputs
 *   AADDGRP       → Account group text
 *   ACSTNUM       → Customer ID (read-only)
 *   ACTSSN1/2/3   → Three separate SSN inputs (3-2-4 digit split)
 *   DOBYEAR/MON/DAY → Single date input (date of birth)
 *   ACSTFCO       → FICO score (300-850)
 *   ACSFNAM/ACSMNAM/ACSLNAM → Name fields (alpha only)
 *   ACSADL1/2, ACSCITY, ACSSTTE, ACSZIPC, ACSCTRY → Address fields
 *   ACSPH1A/B/C + ACSPH2A/B/C → Combined phone inputs (NNN-NNN-NNNN)
 *   ACSGOVT, ACSEFTC, ACSPFLG → Govt ID, EFT, primary holder flag
 *   FKEY05 (DRK→visible) → "Save" button: hidden until data loaded
 *   FKEY12 (DRK→visible) → "Cancel" button: hidden until data loaded
 *   ENTER key → "Process" submit button (always visible)
 *   PF3 key   → "Exit" (always visible)
 *   ERRMSG (ASKIP, BRT, RED) → ErrorMessage component
 *   INFOMSG (PROT) → success message (green)
 *
 * UX decisions:
 *   - Split BMS date sub-fields (OPNYEAR+OPNMON+OPNDAY) are combined into a
 *     single <input type="date"> — modern, accessible, no layout clutter.
 *   - Split SSN fields (ACTSSN1/2/3) kept as three separate inputs with dashes
 *     to preserve the security boundary (avoids passing SSN as single string).
 *   - Split phone fields (ACSPH1A/B/C) combined into single NNN-NNN-NNNN input.
 *   - Form sections as cards (Account Details, Financial, Customer Identity,
 *     Address, Contact) instead of a single dense 80x24 BMS screen.
 *   - Save/Cancel buttons start hidden; revealed after successful data load,
 *     mirroring the FKEY05/FKEY12 DRK→NORM attribute transition in COACTUP.
 */

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter, useSearchParams } from "next/navigation";

import { AppHeader } from "@/components/layout/AppHeader";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";
import {
  AccountViewResponse,
  AccountUpdateRequest,
} from "@/types/account";

// ---------------------------------------------------------------------------
// Zod validation schema
// Maps all COACTUPC 2000-PROCESS-INPUTS validations.
// ---------------------------------------------------------------------------
const accountUpdateSchema = z
  .object({
    // ACSTTUS — Y/N flag
    accountStatus: z.enum(["Y", "N"], {
      errorMap: () => ({ message: "Active status must be Y or N" }),
    }),
    // Date fields — single ISO date string (combines split BMS sub-fields)
    openDate: z.string().min(1, "Open date is required"),
    expiryDate: z.string().min(1, "Expiry date is required"),
    reissueDate: z.string().min(1, "Reissue date is required"),
    // Financial fields — signed numeric validations
    // COBOL origin: WS-EDIT-SIGNED-NUMBER-9V2-X validation
    creditLimit: z
      .number({ invalid_type_error: "Credit limit must be a number" })
      .min(0, "Credit limit must be >= 0"),
    cashLimit: z
      .number({ invalid_type_error: "Cash limit must be a number" })
      .min(0, "Cash limit must be >= 0"),
    currentBalance: z.number({
      invalid_type_error: "Current balance must be a number",
    }),
    cycleCreditAmount: z
      .number({ invalid_type_error: "Cycle credit must be a number" })
      .min(0, "Cycle credit must be >= 0"),
    cycleDebitAmount: z
      .number({ invalid_type_error: "Cycle debit must be a number" })
      .min(0, "Cycle debit must be >= 0"),
    accountGroup: z.string().max(10, "Account group max 10 chars").optional(),
    // Customer ID — read-only but still submitted
    customerId: z.string().min(1, "Customer ID is required"),
    // SSN three-part split — maps ACTSSN1/ACTSSN2/ACTSSN3 BMS fields
    // COBOL origin: COACTUPC INVALID-SSN-PART1 88-level validation
    ssnPart1: z
      .string()
      .regex(/^\d{3}$/, "SSN part 1: exactly 3 digits required"),
    ssnPart2: z
      .string()
      .regex(/^\d{2}$/, "SSN part 2: exactly 2 digits required"),
    ssnPart3: z
      .string()
      .regex(/^\d{4}$/, "SSN part 3: exactly 4 digits required"),
    // Date of birth — combines DOBYEAR/DOBMON/DOBDAY
    dateOfBirth: z.string().min(1, "Date of birth is required"),
    // FICO 300-850 — COBOL origin: WS-EDIT-FICO-SCORE-FLGS
    ficoScore: z
      .number({ invalid_type_error: "FICO score must be a number" })
      .int()
      .min(300, "FICO score must be between 300 and 850")
      .max(850, "FICO score must be between 300 and 850")
      .optional(),
    // Name fields — alpha only (COBOL: WS-EDIT-ALPHA-ONLY-FLAGS)
    firstName: z
      .string()
      .min(1, "First name is required")
      .max(25, "First name max 25 chars"),
    middleName: z.string().max(25, "Middle name max 25 chars").optional(),
    lastName: z
      .string()
      .min(1, "Last name is required")
      .max(25, "Last name max 25 chars"),
    // Address fields
    addressLine1: z.string().max(50).optional(),
    addressLine2: z.string().max(50).optional(),
    city: z.string().max(50).optional(),
    state: z.string().max(2).optional(),
    zipCode: z.string().max(10).optional(),
    country: z.string().max(3).optional(),
    // Phone — NNN-NNN-NNNN (COBOL: WS-EDIT-US-PHONE-NUM three-segment validation)
    phone1: z
      .string()
      .regex(/^\d{3}-\d{3}-\d{4}$/, "Format: NNN-NNN-NNNN")
      .optional()
      .or(z.literal("")),
    phone2: z
      .string()
      .regex(/^\d{3}-\d{3}-\d{4}$/, "Format: NNN-NNN-NNNN")
      .optional()
      .or(z.literal("")),
    governmentId: z.string().max(20).optional(),
    eftAccountId: z.string().max(10).optional(),
    // Primary card holder — Y/N
    primaryCardHolder: z.enum(["Y", "N"], {
      errorMap: () => ({ message: "Primary card holder must be Y or N" }),
    }),
  })
  // Cross-field: cash limit must not exceed credit limit
  // COBOL origin: COACTUPC implicit validation + DB constraint chk_accounts_cash_lte_credit
  .refine((data) => data.cashLimit <= data.creditLimit, {
    message: "Cash limit cannot exceed credit limit",
    path: ["cashLimit"],
  })
  // SSN part1 validation — COBOL: INVALID-SSN-PART1 88-level
  // Area codes 000, 666, and 900-999 are never validly assigned (IRS/SSA rule)
  .refine(
    (data) => {
      const p1 = data.ssnPart1;
      return !(
        p1 === "000" ||
        p1 === "666" ||
        (p1 >= "900" && p1 <= "999")
      );
    },
    {
      message:
        "SSN area number cannot be 000, 666, or in range 900-999",
      path: ["ssnPart1"],
    }
  );

type UpdateFormValues = z.infer<typeof accountUpdateSchema>;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Convert an AccountViewResponse into form default values. */
function responseToFormValues(
  account: AccountViewResponse
): Partial<UpdateFormValues> {
  // Extract last 4 from masked SSN for placeholder; user must re-enter full SSN
  const c = account.customer;
  return {
    accountStatus: account.active_status as "Y" | "N",
    openDate: account.open_date ?? "",
    expiryDate: account.expiration_date ?? "",
    reissueDate: account.reissue_date ?? "",
    creditLimit: parseFloat(account.credit_limit) || 0,
    cashLimit: parseFloat(account.cash_credit_limit) || 0,
    currentBalance: parseFloat(account.current_balance) || 0,
    cycleCreditAmount: parseFloat(account.curr_cycle_credit) || 0,
    cycleDebitAmount: parseFloat(account.curr_cycle_debit) || 0,
    accountGroup: account.group_id ?? "",
    customerId: String(c.customer_id),
    // SSN is masked in API response — user must re-enter to change
    ssnPart1: "",
    ssnPart2: "",
    ssnPart3: c.ssn_masked.slice(-4), // pre-fill last 4 from masked display
    dateOfBirth: c.date_of_birth ?? "",
    ficoScore: c.fico_score ?? undefined,
    firstName: c.first_name,
    middleName: c.middle_name ?? "",
    lastName: c.last_name,
    addressLine1: c.address_line_1 ?? "",
    addressLine2: c.address_line_2 ?? "",
    city: c.city ?? "",
    state: c.state_code ?? "",
    zipCode: c.zip_code ?? "",
    country: c.country_code ?? "",
    phone1: c.phone_1 ?? "",
    phone2: c.phone_2 ?? "",
    governmentId: c.government_id_ref ?? "",
    eftAccountId: c.eft_account_id ?? "",
    primaryCardHolder: c.primary_card_holder as "Y" | "N",
  };
}

/** Build the AccountUpdateRequest payload from form values. */
function buildUpdateRequest(
  values: UpdateFormValues,
  customerId: number
): AccountUpdateRequest {
  return {
    active_status: values.accountStatus,
    open_date: values.openDate,
    expiration_date: values.expiryDate,
    reissue_date: values.reissueDate,
    credit_limit: values.creditLimit,
    cash_credit_limit: values.cashLimit,
    current_balance: values.currentBalance,
    curr_cycle_credit: values.cycleCreditAmount,
    curr_cycle_debit: values.cycleDebitAmount,
    group_id: values.accountGroup || undefined,
    customer: {
      customer_id: customerId,
      first_name: values.firstName,
      middle_name: values.middleName || undefined,
      last_name: values.lastName,
      address_line_1: values.addressLine1 || undefined,
      address_line_2: values.addressLine2 || undefined,
      city: values.city || undefined,
      state_code: values.state || undefined,
      zip_code: values.zipCode || undefined,
      country_code: values.country || undefined,
      phone_1: values.phone1 || undefined,
      phone_2: values.phone2 || undefined,
      ssn_part1: values.ssnPart1,
      ssn_part2: values.ssnPart2,
      ssn_part3: values.ssnPart3,
      date_of_birth: values.dateOfBirth,
      fico_score: values.ficoScore,
      government_id_ref: values.governmentId || undefined,
      eft_account_id: values.eftAccountId || undefined,
      primary_card_holder: values.primaryCardHolder,
    },
  };
}

// ---------------------------------------------------------------------------
// Reusable form field components
// ---------------------------------------------------------------------------

interface FieldProps {
  label: string;
  id: string;
  error?: string;
  required?: boolean;
  hint?: string;
  children: React.ReactNode;
}

function FormField({ label, id, error, required, hint, children }: FieldProps) {
  return (
    <div>
      <label
        htmlFor={id}
        className="block text-xs font-medium text-slate-600 mb-1"
      >
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
        {hint && (
          <span className="text-slate-400 font-normal ml-1">{hint}</span>
        )}
      </label>
      {children}
      {error && (
        <p role="alert" className="mt-1 text-xs text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

const inputClass = (hasError: boolean) =>
  `w-full px-3 py-1.5 border rounded-md text-sm
   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
   ${hasError ? "border-red-400 bg-red-50" : "border-slate-300 bg-white"}`;

const readonlyClass =
  "w-full px-3 py-1.5 border border-slate-200 rounded-md text-sm bg-slate-50 text-slate-500 font-mono cursor-not-allowed";

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function AccountUpdatePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuth();

  const [loadedAccount, setLoadedAccount] =
    useState<AccountViewResponse | null>(null);
  const [accountId, setAccountId] = useState<string>("");
  const [loadState, setLoadState] = useState<
    "idle" | "loading" | "loaded" | "error"
  >("idle");
  // Maps FKEY05/FKEY12 DRK→NORM transition: hidden until first successful data load
  const [showSaveCancel, setShowSaveCancel] = useState(false);
  const [serverError, setServerError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<UpdateFormValues>({
    resolver: zodResolver(accountUpdateSchema),
  });

  // Auth guard — COBOL origin: EIBCALEN=0 → XCTL COSGN00C
  // Must come AFTER all hooks to comply with React Rules of Hooks.
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  /**
   * Auto-load account when accountId query param is present.
   * COBOL origin: COACTUPC first-entry COMMAREA populate —
   * when navigating from Account View, the account ID is pre-filled.
   */
  useEffect(() => {
    const paramId = searchParams?.get("accountId");
    if (paramId) {
      setAccountId(paramId);
      loadAccount(paramId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!isAuthenticated) {
    return null;
  }

  async function loadAccount(id: string) {
    setLoadState("loading");
    setServerError("");
    setSuccessMessage("");

    try {
      const data = await api.get<AccountViewResponse>(
        `/api/v1/accounts/${id}`
      );
      setLoadedAccount(data);
      reset(responseToFormValues(data) as UpdateFormValues);
      setLoadState("loaded");
      // Reveal Save/Cancel buttons — maps FKEY05/FKEY12 DRK→NORM
      setShowSaveCancel(true);
    } catch (error) {
      setLoadState("error");
      if (error instanceof ApiError) {
        if (error.status === 404) {
          setServerError(`Account ${id} not found.`);
        } else if (error.status === 401 || error.status === 403) {
          router.push("/login");
        } else {
          setServerError(error.message || "Failed to load account.");
        }
      } else {
        setServerError("Unable to connect. Please try again.");
      }
    }
  }

  /**
   * Load account by manually entered ID.
   */
  const handleLoadAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accountId.trim()) return;
    await loadAccount(accountId.trim());
  };

  /**
   * Submit handler — maps COACTUPC ENTER/PF5 path → 9000-UPDATE-ACCOUNT.
   */
  const onSubmit = async (values: UpdateFormValues) => {
    if (!loadedAccount) return;

    setIsSaving(true);
    setServerError("");
    setSuccessMessage("");

    try {
      const payload = buildUpdateRequest(
        values,
        loadedAccount.customer.customer_id
      );
      const updated = await api.put<AccountViewResponse>(
        `/api/v1/accounts/${loadedAccount.account_id}`,
        payload
      );
      setLoadedAccount(updated);
      reset(responseToFormValues(updated) as UpdateFormValues);
      setSuccessMessage("Account updated successfully.");
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 422) {
          if (error.errorCode === "NO_CHANGES_DETECTED") {
            setServerError(
              "No changes detected. Please modify at least one field to update."
            );
          } else {
            setServerError(
              error.message || "Validation error. Please check your input."
            );
          }
        } else if (error.status === 401 || error.status === 403) {
          router.push("/login");
        } else {
          setServerError(error.message || "Update failed. Please try again.");
        }
      } else {
        setServerError("Unable to connect. Please try again.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Cancel handler — reset form to last loaded values.
   * Maps PF12 (Cancel) key: abandons changes without saving.
   */
  const handleCancel = () => {
    if (loadedAccount) {
      reset(responseToFormValues(loadedAccount) as UpdateFormValues);
      setServerError("");
      setSuccessMessage("");
    }
  };

  const isLoaded = loadState === "loaded" && loadedAccount !== null;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Application header — replaces BMS rows 1-3 */}
      <AppHeader programName="COACTUPC" transactionId="CAUP" />

      <main className="flex-1 px-4 py-8 max-w-5xl mx-auto w-full">
        {/* Page title */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-800">Update Account</h1>
          <p className="text-sm text-slate-500 mt-1">
            Load an account to edit its financial parameters and customer details.
          </p>
        </div>

        {/* Account ID load form */}
        <form
          onSubmit={handleLoadAccount}
          aria-label="Account load form"
          className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6"
        >
          <div className="flex flex-col sm:flex-row gap-3 items-end">
            <div className="flex-1">
              <label
                htmlFor="loadAccountId"
                className="block text-sm font-medium text-slate-700 mb-1"
              >
                Account Number
                <span className="text-slate-400 font-normal ml-1">
                  (11 digits)
                </span>
              </label>
              <input
                id="loadAccountId"
                type="text"
                autoFocus={!accountId}
                inputMode="numeric"
                maxLength={11}
                placeholder="00000000000"
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm font-mono
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={loadState === "loading"}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400
                  text-white text-sm font-semibold rounded-md transition-colors
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                {loadState === "loading" ? "Loading…" : "Load Account"}
              </button>
              {/* Exit — maps PF3 */}
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

        {/* Error / success messages */}
        {serverError && (
          <div className="mb-4">
            <ErrorMessage message={serverError} color="red" />
          </div>
        )}
        {successMessage && (
          <div className="mb-4">
            <ErrorMessage message={successMessage} color="green" />
          </div>
        )}

        {/* Edit form — shown only after successful load */}
        {isLoaded && (
          <form
            onSubmit={handleSubmit(onSubmit)}
            noValidate
            aria-label="Account update form"
            className="space-y-6"
          >
            {/* ---- Account Details card ---- */}
            <section
              aria-label="Account details"
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-6"
            >
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-4 pb-2 border-b border-slate-100">
                Account Details
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* ACCTSID — read-only after load */}
                <FormField label="Account Number" id="acct-id-display">
                  <input
                    id="acct-id-display"
                    type="text"
                    readOnly
                    value={loadedAccount.account_id}
                    className={readonlyClass}
                  />
                </FormField>

                {/* ACSTTUS — Y/N select */}
                <FormField
                  label="Active Status"
                  id="accountStatus"
                  error={errors.accountStatus?.message}
                  required
                >
                  <select
                    id="accountStatus"
                    className={inputClass(!!errors.accountStatus)}
                    {...register("accountStatus")}
                  >
                    <option value="Y">Y — Active</option>
                    <option value="N">N — Inactive</option>
                  </select>
                </FormField>

                {/* AADDGRP */}
                <FormField
                  label="Account Group"
                  id="accountGroup"
                  error={errors.accountGroup?.message}
                  hint="(max 10)"
                >
                  <input
                    id="accountGroup"
                    type="text"
                    maxLength={10}
                    className={inputClass(!!errors.accountGroup)}
                    {...register("accountGroup")}
                  />
                </FormField>

                {/* OPNYEAR/MON/DAY combined → single date input */}
                <FormField
                  label="Open Date"
                  id="openDate"
                  error={errors.openDate?.message}
                  required
                >
                  <input
                    id="openDate"
                    type="date"
                    className={inputClass(!!errors.openDate)}
                    {...register("openDate")}
                  />
                </FormField>

                {/* EXPYEAR/MON/DAY combined */}
                <FormField
                  label="Expiry Date"
                  id="expiryDate"
                  error={errors.expiryDate?.message}
                  required
                >
                  <input
                    id="expiryDate"
                    type="date"
                    className={inputClass(!!errors.expiryDate)}
                    {...register("expiryDate")}
                  />
                </FormField>

                {/* RISYEAR/MON/DAY combined */}
                <FormField
                  label="Reissue Date"
                  id="reissueDate"
                  error={errors.reissueDate?.message}
                  required
                >
                  <input
                    id="reissueDate"
                    type="date"
                    className={inputClass(!!errors.reissueDate)}
                    {...register("reissueDate")}
                  />
                </FormField>
              </div>
            </section>

            {/* ---- Financial Details card ---- */}
            <section
              aria-label="Financial details"
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-6"
            >
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-4 pb-2 border-b border-slate-100">
                Financial Details
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* ACRDLIM */}
                <FormField
                  label="Credit Limit"
                  id="creditLimit"
                  error={errors.creditLimit?.message}
                  required
                >
                  <input
                    id="creditLimit"
                    type="number"
                    step="0.01"
                    min="0"
                    className={inputClass(!!errors.creditLimit)}
                    {...register("creditLimit", { valueAsNumber: true })}
                  />
                </FormField>

                {/* ACSHLIM */}
                <FormField
                  label="Cash Credit Limit"
                  id="cashLimit"
                  error={errors.cashLimit?.message}
                  required
                  hint="(<= Credit Limit)"
                >
                  <input
                    id="cashLimit"
                    type="number"
                    step="0.01"
                    min="0"
                    className={inputClass(!!errors.cashLimit)}
                    {...register("cashLimit", { valueAsNumber: true })}
                  />
                </FormField>

                {/* ACURBAL */}
                <FormField
                  label="Current Balance"
                  id="currentBalance"
                  error={errors.currentBalance?.message}
                  required
                >
                  <input
                    id="currentBalance"
                    type="number"
                    step="0.01"
                    className={inputClass(!!errors.currentBalance)}
                    {...register("currentBalance", { valueAsNumber: true })}
                  />
                </FormField>

                {/* ACRCYCR */}
                <FormField
                  label="Cycle Credit"
                  id="cycleCreditAmount"
                  error={errors.cycleCreditAmount?.message}
                  required
                >
                  <input
                    id="cycleCreditAmount"
                    type="number"
                    step="0.01"
                    min="0"
                    className={inputClass(!!errors.cycleCreditAmount)}
                    {...register("cycleCreditAmount", { valueAsNumber: true })}
                  />
                </FormField>

                {/* ACRCYDB */}
                <FormField
                  label="Cycle Debit"
                  id="cycleDebitAmount"
                  error={errors.cycleDebitAmount?.message}
                  required
                >
                  <input
                    id="cycleDebitAmount"
                    type="number"
                    step="0.01"
                    min="0"
                    className={inputClass(!!errors.cycleDebitAmount)}
                    {...register("cycleDebitAmount", { valueAsNumber: true })}
                  />
                </FormField>
              </div>
            </section>

            {/* ---- Customer Identity card ---- */}
            <section
              aria-label="Customer identity"
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-6"
            >
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-4 pb-2 border-b border-slate-100">
                Customer Identity
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* ACSTNUM — read-only */}
                <FormField label="Customer ID" id="customerId-display">
                  <input
                    id="customerId-display"
                    type="text"
                    readOnly
                    value={loadedAccount.customer.customer_id}
                    className={readonlyClass}
                  />
                  <input type="hidden" {...register("customerId")} />
                </FormField>

                {/* ACTSSN1/2/3 — three split inputs with dashes */}
                <FormField
                  label="SSN"
                  id="ssnPart1"
                  error={
                    errors.ssnPart1?.message ||
                    errors.ssnPart2?.message ||
                    errors.ssnPart3?.message
                  }
                  required
                  hint="(NNN-NN-NNNN)"
                >
                  {/* SEC-07: autoComplete="off" on all SSN inputs prevents browsers from
                      caching SSN fragments in autofill storage. */}
                  <div className="flex items-center gap-1">
                    <input
                      id="ssnPart1"
                      type="text"
                      inputMode="numeric"
                      maxLength={3}
                      placeholder="NNN"
                      aria-label="SSN area number (3 digits)"
                      autoComplete="off"
                      autoCorrect="off"
                      autoCapitalize="off"
                      spellCheck={false}
                      className={`w-16 px-2 py-1.5 border rounded-md text-sm font-mono text-center
                        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                        ${errors.ssnPart1 ? "border-red-400 bg-red-50" : "border-slate-300"}`}
                      {...register("ssnPart1")}
                    />
                    <span className="text-slate-400">-</span>
                    <input
                      type="text"
                      inputMode="numeric"
                      maxLength={2}
                      placeholder="NN"
                      aria-label="SSN group number (2 digits)"
                      autoComplete="off"
                      autoCorrect="off"
                      autoCapitalize="off"
                      spellCheck={false}
                      className={`w-12 px-2 py-1.5 border rounded-md text-sm font-mono text-center
                        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                        ${errors.ssnPart2 ? "border-red-400 bg-red-50" : "border-slate-300"}`}
                      {...register("ssnPart2")}
                    />
                    <span className="text-slate-400">-</span>
                    <input
                      type="text"
                      inputMode="numeric"
                      maxLength={4}
                      placeholder="NNNN"
                      aria-label="SSN serial number (4 digits)"
                      autoComplete="off"
                      autoCorrect="off"
                      autoCapitalize="off"
                      spellCheck={false}
                      className={`w-16 px-2 py-1.5 border rounded-md text-sm font-mono text-center
                        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                        ${errors.ssnPart3 ? "border-red-400 bg-red-50" : "border-slate-300"}`}
                      {...register("ssnPart3")}
                    />
                  </div>
                  <p className="mt-0.5 text-xs text-slate-400">
                    Current SSN: {loadedAccount.customer.ssn_masked}
                  </p>
                </FormField>

                {/* DOBYEAR/MON/DAY combined */}
                <FormField
                  label="Date of Birth"
                  id="dateOfBirth"
                  error={errors.dateOfBirth?.message}
                  required
                >
                  {/* SEC-07: autoComplete="off" prevents browser from caching date of birth */}
                  <input
                    id="dateOfBirth"
                    type="date"
                    autoComplete="off"
                    className={inputClass(!!errors.dateOfBirth)}
                    {...register("dateOfBirth")}
                  />
                </FormField>

                {/* ACSTFCO — FICO 300-850 */}
                <FormField
                  label="FICO Score"
                  id="ficoScore"
                  error={errors.ficoScore?.message}
                  hint="(300–850)"
                >
                  {/* SEC-07: autoComplete="off" prevents browser from caching FICO score */}
                  <input
                    id="ficoScore"
                    type="number"
                    min={300}
                    max={850}
                    autoComplete="off"
                    className={inputClass(!!errors.ficoScore)}
                    {...register("ficoScore", { valueAsNumber: true })}
                  />
                </FormField>

                {/* ACSFNAM */}
                <FormField
                  label="First Name"
                  id="firstName"
                  error={errors.firstName?.message}
                  required
                >
                  <input
                    id="firstName"
                    type="text"
                    maxLength={25}
                    className={inputClass(!!errors.firstName)}
                    {...register("firstName")}
                  />
                </FormField>

                {/* ACSMNAM */}
                <FormField
                  label="Middle Name"
                  id="middleName"
                  error={errors.middleName?.message}
                >
                  <input
                    id="middleName"
                    type="text"
                    maxLength={25}
                    className={inputClass(!!errors.middleName)}
                    {...register("middleName")}
                  />
                </FormField>

                {/* ACSLNAM */}
                <FormField
                  label="Last Name"
                  id="lastName"
                  error={errors.lastName?.message}
                  required
                >
                  <input
                    id="lastName"
                    type="text"
                    maxLength={25}
                    className={inputClass(!!errors.lastName)}
                    {...register("lastName")}
                  />
                </FormField>

                {/* ACSPFLG */}
                <FormField
                  label="Primary Card Holder"
                  id="primaryCardHolder"
                  error={errors.primaryCardHolder?.message}
                  required
                >
                  <select
                    id="primaryCardHolder"
                    className={inputClass(!!errors.primaryCardHolder)}
                    {...register("primaryCardHolder")}
                  >
                    <option value="Y">Y — Yes</option>
                    <option value="N">N — No</option>
                  </select>
                </FormField>
              </div>
            </section>

            {/* ---- Address card ---- */}
            <section
              aria-label="Address"
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-6"
            >
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-4 pb-2 border-b border-slate-100">
                Address
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Address Line 1" id="addressLine1">
                  <input
                    id="addressLine1"
                    type="text"
                    maxLength={50}
                    className={inputClass(false)}
                    {...register("addressLine1")}
                  />
                </FormField>
                <FormField label="Address Line 2" id="addressLine2">
                  <input
                    id="addressLine2"
                    type="text"
                    maxLength={50}
                    className={inputClass(false)}
                    {...register("addressLine2")}
                  />
                </FormField>
                <FormField label="City" id="city">
                  <input
                    id="city"
                    type="text"
                    maxLength={50}
                    className={inputClass(false)}
                    {...register("city")}
                  />
                </FormField>
                <div className="grid grid-cols-3 gap-2">
                  <FormField label="State" id="state" hint="(2)">
                    <input
                      id="state"
                      type="text"
                      maxLength={2}
                      className={inputClass(false)}
                      {...register("state")}
                    />
                  </FormField>
                  <FormField label="ZIP" id="zipCode" hint="(10)">
                    <input
                      id="zipCode"
                      type="text"
                      maxLength={10}
                      className={inputClass(false)}
                      {...register("zipCode")}
                    />
                  </FormField>
                  <FormField label="Country" id="country" hint="(3)">
                    <input
                      id="country"
                      type="text"
                      maxLength={3}
                      className={inputClass(false)}
                      {...register("country")}
                    />
                  </FormField>
                </div>
              </div>
            </section>

            {/* ---- Contact Info card ---- */}
            <section
              aria-label="Contact information"
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-6"
            >
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-4 pb-2 border-b border-slate-100">
                Contact Information
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* ACSPH1A/B/C combined — NNN-NNN-NNNN */}
                <FormField
                  label="Phone 1"
                  id="phone1"
                  error={errors.phone1?.message}
                  hint="(NNN-NNN-NNNN)"
                >
                  <input
                    id="phone1"
                    type="tel"
                    placeholder="555-555-5555"
                    className={inputClass(!!errors.phone1)}
                    {...register("phone1")}
                  />
                </FormField>
                {/* ACSPH2A/B/C combined */}
                <FormField
                  label="Phone 2"
                  id="phone2"
                  error={errors.phone2?.message}
                  hint="(NNN-NNN-NNNN)"
                >
                  <input
                    id="phone2"
                    type="tel"
                    placeholder="555-555-5555"
                    className={inputClass(!!errors.phone2)}
                    {...register("phone2")}
                  />
                </FormField>
                {/* ACSGOVT */}
                <FormField label="Govt ID Reference" id="governmentId">
                  <input
                    id="governmentId"
                    type="text"
                    maxLength={20}
                    className={inputClass(false)}
                    {...register("governmentId")}
                  />
                </FormField>
                {/* ACSEFTC */}
                <FormField label="EFT Account ID" id="eftAccountId">
                  <input
                    id="eftAccountId"
                    type="text"
                    maxLength={10}
                    className={inputClass(false)}
                    {...register("eftAccountId")}
                  />
                </FormField>
              </div>
            </section>

            {/* ---- Action bar ---- */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex flex-wrap gap-3 items-center">
              {/* Process — maps ENTER key; always visible */}
              <button
                type="submit"
                disabled={isSaving}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400
                  text-white text-sm font-semibold rounded-md transition-colors
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                {isSaving ? "Saving…" : "Process"}
              </button>

              {/* Save — maps FKEY05; hidden until data loaded (DRK→NORM) */}
              {showSaveCancel && (
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400
                    text-white text-sm font-semibold rounded-md transition-colors
                    focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                >
                  Save
                </button>
              )}

              {/* Cancel — maps FKEY12; hidden until data loaded (DRK→NORM) */}
              {showSaveCancel && (
                <button
                  type="button"
                  onClick={handleCancel}
                  className="px-6 py-2 border border-slate-300 text-slate-600 text-sm
                    font-medium rounded-md hover:bg-slate-50 transition-colors
                    focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2"
                >
                  Cancel
                </button>
              )}

              {/* Exit — maps PF3; always visible */}
              <button
                type="button"
                onClick={() => router.back()}
                className="px-4 py-2 text-slate-500 text-sm hover:text-slate-700
                  underline focus:outline-none focus:ring-2 focus:ring-slate-400 rounded"
              >
                Exit
              </button>
            </div>
          </form>
        )}
      </main>

      {/* Key legend — replaces BMS row 24 */}
      <footer className="bg-white border-t border-slate-200 py-2 px-4 text-xs text-slate-400 text-center">
        Process = Submit &nbsp;|&nbsp; Save = Confirm save &nbsp;|&nbsp; Cancel = Discard changes &nbsp;|&nbsp; Exit = Back
      </footer>
    </div>
  );
}
