/**
 * AccountUpdateClient — the full COACTUPC state machine as a React component.
 *
 * Manages:
 *   - Fetching account data (ACUP-DETAILS-NOT-FETCHED → ACUP-SHOW-DETAILS)
 *   - Editing (ACUP-SHOW-DETAILS → ACUP-CHANGES-NOT-OK / ACUP-CHANGES-OK-NOT-CONFIRMED)
 *   - Confirmation step (matches F5=Save gating in COACTUPC)
 *   - Submitting (9600-WRITE-PROCESSING → ACUP-CHANGES-OKAYED-AND-DONE)
 *   - Error display (ERRMSG field = bright red, row 23)
 *   - Info message (INFOMSG field = neutral, row 22)
 */

"use client";

import { useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import Link from "next/link";

import { useAccountUpdate } from "@/hooks/useAccountUpdate";
import { accountUpdateSchema, type AccountUpdateFormData } from "@/lib/validationSchemas";
import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Button } from "@/components/ui/Button";
import { ReadOnlyField } from "@/components/ui/ReadOnlyField";

interface Props {
  acctId: string;
}

export function AccountUpdateClient({ acctId }: Props) {
  const {
    state,
    account,
    defaultValues,
    infoMessage,
    errorMessage,
    fetchAccount,
    requestConfirm,
    cancelConfirm,
    submitUpdate,
    reset,
  } = useAccountUpdate();

  const form = useForm<AccountUpdateFormData>({
    resolver: zodResolver(accountUpdateSchema),
    defaultValues: defaultValues ?? {},
  });

  // Reset form when we receive new data from server
  useEffect(() => {
    if (defaultValues) {
      form.reset(defaultValues);
    }
  }, [defaultValues, form]);

  // Show toast on success
  useEffect(() => {
    if (state === "done") {
      toast.success("Changes committed to database");
    }
    if (state === "failed" && errorMessage) {
      toast.error(errorMessage);
    }
  }, [state, errorMessage]);

  // Auto-fetch when mounted with an acctId
  useEffect(() => {
    if (acctId) {
      fetchAccount(acctId);
    }
  }, [acctId, fetchAccount]);

  const isEditable = state === "show" || state === "editing";
  const isConfirming = state === "confirming";
  const isSaving = state === "saving";
  const isDone = state === "done";

  async function handleFormSubmit(data: AccountUpdateFormData) {
    if (isConfirming) {
      await submitUpdate(data);
    } else {
      requestConfirm();
    }
  }

  function handleCancel() {
    if (isConfirming) {
      cancelConfirm();
    } else {
      reset();
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <ScreenHeader
        tranId="CAUP"
        progName="COACTUPC"
        title01="AWS CardDemo"
        title02="Account Update"
      />

      <main className="flex-1 p-4 max-w-4xl mx-auto w-full">
        <SectionHeader title="Update Account" />

        {/* INFOMSG (row 22) */}
        <div className="mt-2 text-center text-sm text-gray-500" aria-live="polite">
          {infoMessage}
        </div>

        {/* ERRMSG (row 23) — bright red */}
        {errorMessage && (
          <div
            className="mt-1 rounded border border-red-400 bg-red-50 px-3 py-1 text-sm font-semibold text-red-700"
            role="alert"
          >
            {errorMessage}
          </div>
        )}

        {/* Loading state */}
        {state === "loading" && (
          <div className="mt-8 flex justify-center">
            <span className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          </div>
        )}

        {/* Done state */}
        {isDone && (
          <div className="mt-6 text-center space-y-4">
            <p className="text-green-700 font-semibold">
              Changes committed to database
            </p>
            <div className="flex gap-4 justify-center">
              <Button onClick={reset} variant="primary">
                Update Another Account
              </Button>
              <Link href={`/accounts/${account?.acct_id}`}>
                <Button variant="secondary">View Account</Button>
              </Link>
            </div>
          </div>
        )}

        {/* Main edit form */}
        {(isEditable || isConfirming || isSaving) && account && (
          <form
            onSubmit={form.handleSubmit(handleFormSubmit)}
            aria-label="Account Update Form"
            noValidate
          >
            {/* Row 5: Account number (display-only) + status */}
            <div className="mt-3 grid grid-cols-2 gap-x-8 gap-y-3 border-t pt-3">
              <div className="flex items-end gap-4">
                <ReadOnlyField label="Account Number" value={account.acct_id} className="flex-1" />
                <div className="w-24">
                  <Label htmlFor="acct_active_status" required>Active Y/N</Label>
                  <Controller
                    name="acct_active_status"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="acct_active_status"
                        maxLength={1}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                        className="uppercase"
                      />
                    )}
                  />
                </div>
              </div>

              {/* Opened date */}
              <div className="flex items-end gap-4">
                <div className="flex-1">
                  <Label htmlFor="acct_open_date">Opened</Label>
                  <Controller
                    name="acct_open_date"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        id="acct_open_date"
                        type="date"
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                      />
                    )}
                  />
                </div>
                <div className="flex-1">
                  <Label htmlFor="acct_credit_limit" required>Credit Limit</Label>
                  <Controller
                    name="acct_credit_limit"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="acct_credit_limit"
                        type="number"
                        step="0.01"
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                        className="text-right font-mono"
                      />
                    )}
                  />
                </div>
              </div>

              {/* Expiry + Cash Credit Limit */}
              <div className="flex items-end gap-4">
                <div className="flex-1">
                  <Label htmlFor="acct_expiration_date">Expiry</Label>
                  <Controller
                    name="acct_expiration_date"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        id="acct_expiration_date"
                        type="date"
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                      />
                    )}
                  />
                </div>
                <div className="flex-1">
                  <Label htmlFor="acct_cash_credit_limit" required>Cash Credit Limit</Label>
                  <Controller
                    name="acct_cash_credit_limit"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="acct_cash_credit_limit"
                        type="number"
                        step="0.01"
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                        className="text-right font-mono"
                      />
                    )}
                  />
                </div>
              </div>

              {/* Reissue + Current Balance */}
              <div className="flex items-end gap-4">
                <div className="flex-1">
                  <Label htmlFor="acct_reissue_date">Reissue</Label>
                  <Controller
                    name="acct_reissue_date"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        id="acct_reissue_date"
                        type="date"
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                      />
                    )}
                  />
                </div>
                <div className="flex-1">
                  <Label htmlFor="acct_curr_bal" required>Current Balance</Label>
                  <Controller
                    name="acct_curr_bal"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="acct_curr_bal"
                        type="number"
                        step="0.01"
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                        className="text-right font-mono"
                      />
                    )}
                  />
                </div>
              </div>

              {/* Current Cycle Credit */}
              <div className="col-start-2">
                <Label htmlFor="acct_curr_cyc_credit" required>Current Cycle Credit</Label>
                <Controller
                  name="acct_curr_cyc_credit"
                  control={form.control}
                  render={({ field, fieldState }) => (
                    <Input
                      {...field}
                      id="acct_curr_cyc_credit"
                      type="number"
                      step="0.01"
                      disabled={!isEditable}
                      error={fieldState.error?.message}
                      className="text-right font-mono"
                    />
                  )}
                />
              </div>

              {/* Account Group + Current Cycle Debit */}
              <div className="flex items-end gap-4">
                <div className="flex-1">
                  <Label htmlFor="acct_group_id">Account Group</Label>
                  <Controller
                    name="acct_group_id"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        id="acct_group_id"
                        maxLength={10}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                      />
                    )}
                  />
                </div>
                <div className="flex-1">
                  <Label htmlFor="acct_curr_cyc_debit" required>Current Cycle Debit</Label>
                  <Controller
                    name="acct_curr_cyc_debit"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="acct_curr_cyc_debit"
                        type="number"
                        step="0.01"
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                        className="text-right font-mono"
                      />
                    )}
                  />
                </div>
              </div>
            </div>

            {/* Customer Details section */}
            <div className="mt-4 border-t pt-2">
              <SectionHeader title="Customer Details" className="text-sm" />

              {/* Customer ID (display-only — DFHBMPRF applied in COBOL) */}
              <ReadOnlyField
                label="Customer ID"
                value={account.customer?.cust_id}
                className="mb-2 max-w-[120px]"
              />

              <div className="grid grid-cols-3 gap-x-4 gap-y-3">
                {/* SSN (3 parts — mirrors ACTSSN1/2/3 fields) */}
                <div>
                  <Label required>SSN</Label>
                  <div className="flex gap-1 items-center">
                    <Controller
                      name="cust_ssn.part1"
                      control={form.control}
                      render={({ field, fieldState }) => (
                        <Input
                          {...field}
                          maxLength={3}
                          placeholder="XXX"
                          disabled={!isEditable}
                          error={fieldState.error?.message}
                          className="w-14 font-mono text-center"
                          aria-label="SSN part 1"
                        />
                      )}
                    />
                    <span className="text-gray-400">-</span>
                    <Controller
                      name="cust_ssn.part2"
                      control={form.control}
                      render={({ field, fieldState }) => (
                        <Input
                          {...field}
                          maxLength={2}
                          placeholder="XX"
                          disabled={!isEditable}
                          error={fieldState.error?.message}
                          className="w-10 font-mono text-center"
                          aria-label="SSN part 2"
                        />
                      )}
                    />
                    <span className="text-gray-400">-</span>
                    <Controller
                      name="cust_ssn.part3"
                      control={form.control}
                      render={({ field, fieldState }) => (
                        <Input
                          {...field}
                          maxLength={4}
                          placeholder="XXXX"
                          disabled={!isEditable}
                          error={fieldState.error?.message}
                          className="w-16 font-mono text-center"
                          aria-label="SSN part 3"
                        />
                      )}
                    />
                  </div>
                </div>

                {/* Date of Birth */}
                <div>
                  <Label htmlFor="cust_dob" required>Date of Birth</Label>
                  <Controller
                    name="cust_dob"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="cust_dob"
                        type="date"
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                      />
                    )}
                  />
                </div>

                {/* FICO Score */}
                <div>
                  <Label htmlFor="cust_fico_credit_score" required>FICO Score (300-850)</Label>
                  <Controller
                    name="cust_fico_credit_score"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="cust_fico_credit_score"
                        type="number"
                        min={300}
                        max={850}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                        className="w-24"
                      />
                    )}
                  />
                </div>

                {/* Names */}
                <div>
                  <Label htmlFor="cust_first_name" required>First Name</Label>
                  <Controller
                    name="cust_first_name"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="cust_first_name"
                        maxLength={25}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                      />
                    )}
                  />
                </div>
                <div>
                  <Label htmlFor="cust_middle_name">Middle Name</Label>
                  <Controller
                    name="cust_middle_name"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        id="cust_middle_name"
                        maxLength={25}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                      />
                    )}
                  />
                </div>
                <div>
                  <Label htmlFor="cust_last_name" required>Last Name</Label>
                  <Controller
                    name="cust_last_name"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="cust_last_name"
                        maxLength={25}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                      />
                    )}
                  />
                </div>

                {/* Address line 1 + State */}
                <div className="col-span-2">
                  <Label htmlFor="cust_addr_line_1" required>Address</Label>
                  <Controller
                    name="cust_addr_line_1"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="cust_addr_line_1"
                        maxLength={50}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                      />
                    )}
                  />
                </div>
                <div>
                  <Label htmlFor="cust_addr_state_cd" required>State</Label>
                  <Controller
                    name="cust_addr_state_cd"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="cust_addr_state_cd"
                        maxLength={2}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                        className="uppercase w-16"
                      />
                    )}
                  />
                </div>

                {/* Address line 2 + ZIP */}
                <div className="col-span-2">
                  <Label htmlFor="cust_addr_line_2">Address Line 2</Label>
                  <Controller
                    name="cust_addr_line_2"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        id="cust_addr_line_2"
                        maxLength={50}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                      />
                    )}
                  />
                </div>
                <div>
                  <Label htmlFor="cust_addr_zip" required>ZIP</Label>
                  <Controller
                    name="cust_addr_zip"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="cust_addr_zip"
                        maxLength={10}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                        className="w-28 font-mono"
                      />
                    )}
                  />
                </div>

                {/* City + Country (country protected in COBOL) */}
                <div className="col-span-2">
                  <Label htmlFor="cust_addr_line_3">City</Label>
                  <Controller
                    name="cust_addr_line_3"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        id="cust_addr_line_3"
                        maxLength={50}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                      />
                    )}
                  />
                </div>
                <div>
                  {/* Country is DFHBMPRF-protected in COBOL */}
                  <ReadOnlyField
                    label="Country"
                    value={account.customer?.cust_addr_country_cd}
                  />
                </div>

                {/* Phone 1 (3 sub-fields — mirrors ACSPH1A/B/C) */}
                <div>
                  <Label required>Phone 1 (aaa)bbb-cccc</Label>
                  <div className="flex gap-1 items-center">
                    <span className="text-gray-500">(</span>
                    <Controller
                      name="cust_phone_num_1.area_code"
                      control={form.control}
                      render={({ field, fieldState }) => (
                        <Input
                          {...field}
                          maxLength={3}
                          placeholder="202"
                          disabled={!isEditable}
                          error={fieldState.error?.message}
                          className="w-12 font-mono text-center"
                          aria-label="Phone 1 area code"
                        />
                      )}
                    />
                    <span className="text-gray-500">)</span>
                    <Controller
                      name="cust_phone_num_1.prefix"
                      control={form.control}
                      render={({ field, fieldState }) => (
                        <Input
                          {...field}
                          maxLength={3}
                          placeholder="456"
                          disabled={!isEditable}
                          error={fieldState.error?.message}
                          className="w-12 font-mono text-center"
                          aria-label="Phone 1 prefix"
                        />
                      )}
                    />
                    <span className="text-gray-500">-</span>
                    <Controller
                      name="cust_phone_num_1.line_number"
                      control={form.control}
                      render={({ field, fieldState }) => (
                        <Input
                          {...field}
                          maxLength={4}
                          placeholder="1111"
                          disabled={!isEditable}
                          error={fieldState.error?.message}
                          className="w-16 font-mono text-center"
                          aria-label="Phone 1 line number"
                        />
                      )}
                    />
                  </div>
                </div>

                {/* Government Issued ID */}
                <div className="col-span-2">
                  <Label htmlFor="cust_govt_issued_id">Government Issued ID</Label>
                  <Controller
                    name="cust_govt_issued_id"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        id="cust_govt_issued_id"
                        maxLength={20}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                      />
                    )}
                  />
                </div>

                {/* Phone 2 (optional) */}
                <div>
                  <Label>Phone 2 (optional)</Label>
                  <div className="flex gap-1 items-center">
                    <span className="text-gray-500">(</span>
                    <Controller
                      name="cust_phone_num_2.area_code"
                      control={form.control}
                      render={({ field, fieldState }) => (
                        <Input
                          {...field}
                          value={field.value ?? ""}
                          maxLength={3}
                          placeholder="202"
                          disabled={!isEditable}
                          error={fieldState.error?.message}
                          className="w-12 font-mono text-center"
                          aria-label="Phone 2 area code"
                        />
                      )}
                    />
                    <span className="text-gray-500">)</span>
                    <Controller
                      name="cust_phone_num_2.prefix"
                      control={form.control}
                      render={({ field, fieldState }) => (
                        <Input
                          {...field}
                          value={field.value ?? ""}
                          maxLength={3}
                          placeholder="456"
                          disabled={!isEditable}
                          error={fieldState.error?.message}
                          className="w-12 font-mono text-center"
                          aria-label="Phone 2 prefix"
                        />
                      )}
                    />
                    <span className="text-gray-500">-</span>
                    <Controller
                      name="cust_phone_num_2.line_number"
                      control={form.control}
                      render={({ field, fieldState }) => (
                        <Input
                          {...field}
                          value={field.value ?? ""}
                          maxLength={4}
                          placeholder="1111"
                          disabled={!isEditable}
                          error={fieldState.error?.message}
                          className="w-16 font-mono text-center"
                          aria-label="Phone 2 line number"
                        />
                      )}
                    />
                  </div>
                </div>

                {/* EFT Account ID */}
                <div>
                  <Label htmlFor="cust_eft_account_id" required>EFT Account ID</Label>
                  <Controller
                    name="cust_eft_account_id"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="cust_eft_account_id"
                        maxLength={10}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                        className="font-mono"
                      />
                    )}
                  />
                </div>

                {/* Primary Card Holder */}
                <div>
                  <Label htmlFor="cust_pri_card_holder_ind" required>Primary Card Holder Y/N</Label>
                  <Controller
                    name="cust_pri_card_holder_ind"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Input
                        {...field}
                        id="cust_pri_card_holder_ind"
                        maxLength={1}
                        disabled={!isEditable}
                        error={fieldState.error?.message}
                        className="w-12 uppercase"
                      />
                    )}
                  />
                </div>
              </div>
            </div>

            {/* Confirmation banner — shown when state === 'confirming' */}
            {isConfirming && (
              <div
                className="mt-4 rounded border border-yellow-300 bg-yellow-50 px-4 py-3"
                role="status"
              >
                <p className="text-sm font-semibold text-yellow-800">
                  Changes validated. Press F5=Save to commit or F12=Cancel to go back.
                </p>
              </div>
            )}

            {/* Row 24: Action buttons — mirrors FKEYS / FKEY05 / FKEY12 */}
            <div className="mt-4 border-t pt-3 flex items-center gap-4 text-sm">
              <span className="text-gray-500 text-xs">ENTER=Process</span>

              {isEditable && (
                <Button type="submit" variant="primary" loading={false}>
                  Review Changes
                </Button>
              )}

              {/* F5=Save — only active when confirming (FKEY05 dark until confirmation) */}
              {isConfirming && (
                <Button
                  type="submit"
                  variant="primary"
                  loading={isSaving}
                  className="bg-green-700 hover:bg-green-800"
                  aria-label="F5=Save"
                >
                  F5=Save
                </Button>
              )}

              {/* F12=Cancel — only active when changes made (FKEY12) */}
              {(isEditable || isConfirming) && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleCancel}
                  aria-label="F12=Cancel"
                >
                  F12=Cancel
                </Button>
              )}

              {/* F3=Exit */}
              <Link href="/accounts/update">
                <Button type="button" variant="ghost" aria-label="F3=Exit">
                  F3=Exit
                </Button>
              </Link>
            </div>

            {/* Hidden concurrency token */}
            <input type="hidden" {...form.register("updated_at")} />
          </form>
        )}

        {/* Idle state — show search form */}
        {state === "idle" && !acctId && (
          <div className="mt-6 max-w-lg">
            <p className="text-sm text-gray-500 mb-3">
              Enter or update id of account to update
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
