"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuthStore } from "@/stores/auth-store";
import { getAccount, updateAccount, extractErrorMessage, extractErrorCode } from "@/lib/api";
import { AppHeader } from "@/components/layout/AppHeader";
import { MessageBar } from "@/components/ui/MessageBar";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import type { AccountDetailResponse } from "@/types";

// ---------------------------------------------------------------------------
// Zod schema — mirrors backend AccountUpdateRequest + CustomerUpdateRequest
// ---------------------------------------------------------------------------

const ssnPartSchema = z.object({
  ssn_part1: z
    .string()
    .regex(/^\d{3}$/, "Must be 3 digits")
    .refine((v) => v !== "000", "Cannot be 000")
    .refine((v) => v !== "666", "Cannot be 666")
    .refine((v) => parseInt(v) < 900, "Cannot start with 9")
    .optional()
    .or(z.literal("")),
  ssn_part2: z
    .string()
    .regex(/^\d{2}$/, "Must be 2 digits")
    .refine((v) => v !== "00", "Cannot be 00")
    .optional()
    .or(z.literal("")),
  ssn_part3: z
    .string()
    .regex(/^\d{4}$/, "Must be 4 digits")
    .refine((v) => v !== "0000", "Cannot be 0000")
    .optional()
    .or(z.literal("")),
});

const updateSchema = z
  .object({
    active_status: z.enum(["Y", "N"]),
    credit_limit: z.coerce.number().min(0),
    cash_credit_limit: z.coerce.number().min(0),
    current_balance: z.coerce.number(),
    current_cycle_credit: z.coerce.number().min(0),
    current_cycle_debit: z.coerce.number().min(0),
    group_id: z.string().max(10).optional().or(z.literal("")),
    // Customer fields
    first_name: z.string().min(1, "First name is required").max(25),
    middle_name: z.string().max(25).optional().or(z.literal("")),
    last_name: z.string().min(1, "Last name is required").max(25),
    address: z.string().max(50).optional().or(z.literal("")),
    city: z.string().max(50).optional().or(z.literal("")),
    state: z.string().max(2).optional().or(z.literal("")),
    zip_code: z.string().max(10).optional().or(z.literal("")),
    country: z.string().max(3).optional().or(z.literal("")),
    phone_number: z.string().max(15).optional().or(z.literal("")),
    email: z.string().email("Invalid email").max(50).optional().or(z.literal("")),
    fico_credit_score: z.coerce.number().min(300).max(850).optional(),
    ssn_part1: z.string().optional().or(z.literal("")),
    ssn_part2: z.string().optional().or(z.literal("")),
    ssn_part3: z.string().optional().or(z.literal("")),
  })
  .refine(
    (data) => data.cash_credit_limit <= data.credit_limit,
    {
      message: "Cash credit limit cannot exceed credit limit",
      path: ["cash_credit_limit"],
    }
  );

type UpdateFormValues = z.infer<typeof updateSchema>;

/**
 * Account Update page — COACTUPC.
 * Editable fields: active_status, credit limits, customer name/address/phone/email/fico/SSN.
 * account_id is PROT (read-only, shown for context).
 */
function AccountUpdateContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuthStore();

  const [accountIdInput, setAccountIdInput] = useState(
    searchParams.get("account_id") || ""
  );
  const [account, setAccount] = useState<AccountDetailResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<UpdateFormValues>({
    resolver: zodResolver(updateSchema),
  });

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  useEffect(() => {
    const aid = searchParams.get("account_id");
    if (aid) fetchAccount(Number(aid));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchAccount(accountId: number) {
    setErrorMsg(null);
    setSuccessMsg(null);
    setAccount(null);
    setLoading(true);
    try {
      const data = await getAccount(accountId);
      setAccount(data);
      // Populate form with current values
      reset({
        active_status: data.active_status,
        credit_limit: data.credit_limit,
        cash_credit_limit: data.cash_credit_limit,
        current_balance: data.current_balance,
        current_cycle_credit: data.current_cycle_credit,
        current_cycle_debit: data.current_cycle_debit,
        group_id: data.group_id || "",
        first_name: data.customer.first_name,
        middle_name: data.customer.middle_name || "",
        last_name: data.customer.last_name,
        address: data.customer.address || "",
        city: data.customer.city || "",
        state: data.customer.state || "",
        zip_code: data.customer.zip_code || "",
        country: data.customer.country || "",
        phone_number: data.customer.phone_number || "",
        email: data.customer.email || "",
        fico_credit_score: data.customer.fico_credit_score,
        ssn_part1: "",
        ssn_part2: "",
        ssn_part3: "",
      });
    } catch (err) {
      setErrorMsg(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const id = parseInt(accountIdInput, 10);
    if (isNaN(id) || id <= 0) {
      setErrorMsg("ACCOUNT ID MUST BE A POSITIVE NUMBER");
      return;
    }
    fetchAccount(id);
  }

  async function onSubmit(values: UpdateFormValues) {
    if (!account) return;
    setSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    // Build customer update payload
    const customerPayload: Record<string, unknown> = {
      first_name: values.first_name,
      middle_name: values.middle_name || undefined,
      last_name: values.last_name,
      address: values.address || undefined,
      city: values.city || undefined,
      state: values.state || undefined,
      zip_code: values.zip_code || undefined,
      country: values.country || undefined,
      phone_number: values.phone_number || undefined,
      email: values.email || undefined,
      fico_credit_score: values.fico_credit_score,
    };

    // Include SSN only if all three parts are provided
    if (values.ssn_part1 && values.ssn_part2 && values.ssn_part3) {
      customerPayload.ssn_part1 = values.ssn_part1;
      customerPayload.ssn_part2 = values.ssn_part2;
      customerPayload.ssn_part3 = values.ssn_part3;
    }

    try {
      await updateAccount(account.account_id, {
        active_status: values.active_status,
        credit_limit: values.credit_limit,
        cash_credit_limit: values.cash_credit_limit,
        current_balance: values.current_balance,
        current_cycle_credit: values.current_cycle_credit,
        current_cycle_debit: values.current_cycle_debit,
        group_id: values.group_id || undefined,
        customer: customerPayload as never,
      });
      setSuccessMsg("ACCOUNT UPDATED SUCCESSFULLY");
      // Refresh
      fetchAccount(account.account_id);
    } catch (err) {
      const code = extractErrorCode(err);
      if (code === "NO_CHANGES_DETECTED") {
        setErrorMsg("NO CHANGES DETECTED - RECORD NOT UPDATED");
      } else {
        setErrorMsg(extractErrorMessage(err));
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen bg-mainframe-bg">
      <AppHeader
        title="ACCOUNT UPDATE"
        subtitle="COACTUPC - UPDATE ACCOUNT AND CUSTOMER DETAILS"
      />

      <main className="container mx-auto px-4 py-6 max-w-4xl">
        {/* Search */}
        <form onSubmit={handleSearch} className="border border-mainframe-border p-4 mb-4">
          <div className="flex items-center space-x-4">
            <label className="text-mainframe-dim text-xs w-24">ACCT NUM:</label>
            <input
              type="text"
              value={accountIdInput}
              onChange={(e) => setAccountIdInput(e.target.value)}
              maxLength={11}
              className="px-2 py-1 text-sm w-32"
              placeholder="___________"
            />
            <button
              type="button"
              onClick={handleSearch}
              className="px-4 py-1 text-sm bg-mainframe-border text-mainframe-text hover:bg-mainframe-panel"
            >
              [ FETCH ]
            </button>
          </div>
        </form>

        {/* Messages */}
        {errorMsg && (
          <div className="mb-4">
            <MessageBar type="error" message={errorMsg} onDismiss={() => setErrorMsg(null)} />
          </div>
        )}
        {successMsg && (
          <div className="mb-4">
            <MessageBar type="success" message={successMsg} onDismiss={() => setSuccessMsg(null)} />
          </div>
        )}

        {loading && <LoadingSpinner message="FETCHING ACCOUNT..." />}

        {account && !loading && (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Account fields */}
            <div className="border border-mainframe-border p-4">
              <h2 className="text-mainframe-info text-sm font-bold mb-3 border-b border-mainframe-border pb-2">
                ACCOUNT INFORMATION (ACCT: {account.account_id})
              </h2>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <FormField label="STATUS" error={errors.active_status?.message}>
                  <select {...register("active_status")} className="px-2 py-1 text-sm w-20">
                    <option value="Y">Y - ACTIVE</option>
                    <option value="N">N - INACTIVE</option>
                  </select>
                </FormField>
                <FormField label="CREDIT LIMIT" error={errors.credit_limit?.message}>
                  <input {...register("credit_limit")} type="number" step="0.01" className="px-2 py-1 text-sm w-32" />
                </FormField>
                <FormField label="CASH LIMIT" error={errors.cash_credit_limit?.message}>
                  <input {...register("cash_credit_limit")} type="number" step="0.01" className="px-2 py-1 text-sm w-32" />
                </FormField>
                <FormField label="CURRENT BAL" error={errors.current_balance?.message}>
                  <input {...register("current_balance")} type="number" step="0.01" className="px-2 py-1 text-sm w-32" />
                </FormField>
                <FormField label="CYCLE CREDIT" error={errors.current_cycle_credit?.message}>
                  <input {...register("current_cycle_credit")} type="number" step="0.01" className="px-2 py-1 text-sm w-32" />
                </FormField>
                <FormField label="CYCLE DEBIT" error={errors.current_cycle_debit?.message}>
                  <input {...register("current_cycle_debit")} type="number" step="0.01" className="px-2 py-1 text-sm w-32" />
                </FormField>
                <FormField label="GROUP ID" error={errors.group_id?.message}>
                  <input {...register("group_id")} type="text" maxLength={10} className="px-2 py-1 text-sm w-24" />
                </FormField>
              </div>
            </div>

            {/* Customer fields */}
            <div className="border border-mainframe-border p-4">
              <h2 className="text-mainframe-info text-sm font-bold mb-3 border-b border-mainframe-border pb-2">
                CUSTOMER INFORMATION (CUST: {account.customer.customer_id})
              </h2>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <FormField label="FIRST NAME" error={errors.first_name?.message}>
                  <input {...register("first_name")} type="text" maxLength={25} className="px-2 py-1 text-sm w-40" />
                </FormField>
                <FormField label="MID NAME" error={errors.middle_name?.message}>
                  <input {...register("middle_name")} type="text" maxLength={25} className="px-2 py-1 text-sm w-40" />
                </FormField>
                <FormField label="LAST NAME" error={errors.last_name?.message}>
                  <input {...register("last_name")} type="text" maxLength={25} className="px-2 py-1 text-sm w-40" />
                </FormField>
                <FormField label="SSN (P1-P2-P3)" error={undefined}>
                  <div className="flex items-center space-x-1">
                    <input {...register("ssn_part1")} type="text" maxLength={3} className="px-1 py-1 text-sm w-10" placeholder="NNN" />
                    <span className="text-mainframe-dim">-</span>
                    <input {...register("ssn_part2")} type="text" maxLength={2} className="px-1 py-1 text-sm w-8" placeholder="NN" />
                    <span className="text-mainframe-dim">-</span>
                    <input {...register("ssn_part3")} type="text" maxLength={4} className="px-1 py-1 text-sm w-12" placeholder="NNNN" />
                    <span className="text-mainframe-dim text-xs ml-1">(CURRENT: {account.customer.ssn_masked})</span>
                  </div>
                </FormField>
                <FormField label="ADDRESS" error={errors.address?.message}>
                  <input {...register("address")} type="text" maxLength={50} className="px-2 py-1 text-sm w-56" />
                </FormField>
                <FormField label="CITY" error={errors.city?.message}>
                  <input {...register("city")} type="text" maxLength={50} className="px-2 py-1 text-sm w-40" />
                </FormField>
                <FormField label="STATE" error={errors.state?.message}>
                  <input {...register("state")} type="text" maxLength={2} className="px-2 py-1 text-sm w-12" />
                </FormField>
                <FormField label="ZIP" error={errors.zip_code?.message}>
                  <input {...register("zip_code")} type="text" maxLength={10} className="px-2 py-1 text-sm w-20" />
                </FormField>
                <FormField label="PHONE" error={errors.phone_number?.message}>
                  <input {...register("phone_number")} type="text" maxLength={15} className="px-2 py-1 text-sm w-36" />
                </FormField>
                <FormField label="EMAIL" error={errors.email?.message}>
                  <input {...register("email")} type="text" maxLength={50} className="px-2 py-1 text-sm w-56" />
                </FormField>
                <FormField label="FICO SCORE" error={errors.fico_credit_score?.message}>
                  <input {...register("fico_credit_score")} type="number" min={300} max={850} className="px-2 py-1 text-sm w-20" />
                </FormField>
              </div>
            </div>

            {/* Action bar */}
            <div className="flex items-center justify-between border-t border-mainframe-border pt-4 text-xs">
              <button
                type="button"
                onClick={() => router.push("/menu")}
                className="text-mainframe-dim hover:text-mainframe-text"
              >
                PF3=MENU
              </button>
              <button
                type="button"
                onClick={() =>
                  router.push(`/accounts/view?account_id=${account.account_id}`)
                }
                className="text-mainframe-dim hover:text-mainframe-text"
              >
                PF4=VIEW
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2 bg-mainframe-border text-mainframe-text hover:bg-mainframe-panel disabled:opacity-50 text-sm font-bold"
              >
                {saving ? "SAVING..." : "[ PF5=UPDATE ]"}
              </button>
            </div>
          </form>
        )}
      </main>
    </div>
  );
}

function FormField({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-mainframe-dim mb-1">{label}:</label>
      {children}
      {error && <p className="text-mainframe-error text-xs mt-1">{error}</p>}
    </div>
  );
}

export default function AccountUpdatePage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <AccountUpdateContent />
    </Suspense>
  );
}
