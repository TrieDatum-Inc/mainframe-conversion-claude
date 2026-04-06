"use client";

/**
 * TransactionForm — modern form replacing the COTRN02C BMS data entry screen.
 *
 * COBOL BMS fields → form inputs:
 *   ACTIDIN(11)  → account_id text input
 *   CARDNIN(16)  → card_number text input (either/or with account)
 *   TTYPCD(2)    → type_code
 *   TCATCD(4)    → category_code
 *   TRNSRC(10)   → source
 *   TDESC(60)    → description
 *   TRNAMT(12)   → amount (hint: -99999999.99)
 *   TORIGDT(10)  → original_date (YYYY-MM-DD)
 *   TPROCDT(10)  → processing_date (YYYY-MM-DD)
 *   MID(9)       → merchant_id (numeric only)
 *   MNAME(30)    → merchant_name
 *   MCITY(25)    → merchant_city
 *   MZIP(10)     → merchant_zip
 *   CONFIRM(1)   → confirmation step (Y/N → confirmed boolean)
 *
 * PF5 "Copy Last Transaction" → "Copy Last Transaction" button
 */

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter } from "next/navigation";
import { createTransaction, getLastTransaction } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";

// ---------------------------------------------------------------------------
// Validation schema (mirrors COTRN02C business rules)
// ---------------------------------------------------------------------------
const schema = z
  .object({
    account_id: z.string().max(11).optional().or(z.literal("")),
    card_number: z.string().max(16).optional().or(z.literal("")),
    type_code: z.string().min(1).max(2),
    category_code: z.string().min(1).max(4),
    source: z.string().max(10).default(""),
    description: z.string().max(100).default(""),
    amount: z
      .number({ invalid_type_error: "Amount must be a number" })
      .min(-99999999.99, "Amount too low")
      .max(99999999.99, "Amount too high"),
    original_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Use YYYY-MM-DD format"),
    processing_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Use YYYY-MM-DD format"),
    merchant_id: z
      .string()
      .max(9)
      .refine((v) => !v || /^\d+$/.test(v), "Merchant ID must be digits only")
      .default(""),
    merchant_name: z.string().max(50).default(""),
    merchant_city: z.string().max(50).default(""),
    merchant_zip: z.string().max(10).default(""),
  })
  .refine(
    (d) => d.account_id || d.card_number,
    { message: "Either Account ID or Card Number must be provided", path: ["account_id"] }
  );

type FormValues = z.infer<typeof schema>;

export function TransactionForm() {
  const router = useRouter();
  const [step, setStep] = useState<"form" | "confirm">("form");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    getValues,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      source: "POS TERM",
      original_date: new Date().toISOString().split("T")[0],
      processing_date: new Date().toISOString().split("T")[0],
    },
  });

  // PF5 "Copy Last Transaction" — prefill from most recent transaction for the card
  async function handleCopyLast() {
    const cardNumber = getValues("card_number");
    if (!cardNumber) {
      setError("Enter a card number first to copy the last transaction");
      return;
    }
    setError(null);
    try {
      const last = await getLastTransaction(cardNumber);
      if (!last) {
        setError("No previous transaction found for this card");
        return;
      }
      setValue("type_code", last.type_code);
      setValue("category_code", last.category_code);
      setValue("source", last.source);
      setValue("description", last.description);
      setValue("merchant_id", last.merchant_id);
      setValue("merchant_name", last.merchant_name);
      setValue("merchant_city", last.merchant_city);
      setValue("merchant_zip", last.merchant_zip);
    } catch (e) {
      setError(getErrorMessage(e));
    }
  }

  // First ENTER → validate → go to confirm step (COBOL CONFIRM field)
  function onValidate(data: FormValues) {
    setError(null);
    setStep("confirm");
  }

  // Confirm → submit (CONFIRM='Y')
  async function onConfirm() {
    const data = getValues();
    setIsSubmitting(true);
    setError(null);
    try {
      const result = await createTransaction({
        ...data,
        amount: Number(data.amount),
        confirmed: true,
      });
      router.push(`/transactions/${result.transaction_id}`);
    } catch (e) {
      setError(getErrorMessage(e));
      setStep("form");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (step === "confirm") {
    return <ConfirmStep values={getValues()} onConfirm={onConfirm} onBack={() => setStep("form")} isSubmitting={isSubmitting} />;
  }

  return (
    <form onSubmit={handleSubmit(onValidate)} noValidate className="space-y-6">
      {error && <Alert variant="error" message={error} />}

      {/* Account / Card resolution */}
      <FormSection title="Account / Card">
        <p className="text-sm text-slate-500 mb-4">
          Provide either the Account ID or Card Number — the other will be resolved automatically.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Account ID"
            placeholder="00000001000"
            maxLength={11}
            {...register("account_id")}
            error={errors.account_id?.message}
          />
          <Input
            label="Card Number"
            placeholder="4000002000000000"
            maxLength={16}
            {...register("card_number")}
            error={errors.card_number?.message}
          />
        </div>
      </FormSection>

      {/* Transaction Details */}
      <FormSection title="Transaction Details">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Input
            label="Type Code"
            placeholder="01"
            maxLength={2}
            {...register("type_code")}
            error={errors.type_code?.message}
          />
          <Input
            label="Category Code"
            placeholder="0001"
            maxLength={4}
            {...register("category_code")}
            error={errors.category_code?.message}
          />
          <Input
            label="Source"
            placeholder="POS TERM"
            maxLength={10}
            {...register("source")}
            error={errors.source?.message}
          />
        </div>
        <Input
          label="Description"
          placeholder="Transaction description"
          maxLength={100}
          {...register("description")}
          error={errors.description?.message}
        />
        <Input
          label="Amount"
          type="number"
          step="0.01"
          placeholder="-45.67"
          hint="Format: -99999999.99 (negative for debits)"
          {...register("amount", { valueAsNumber: true })}
          error={errors.amount?.message}
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Original Date"
            type="date"
            hint="YYYY-MM-DD"
            {...register("original_date")}
            error={errors.original_date?.message}
          />
          <Input
            label="Processing Date"
            type="date"
            hint="YYYY-MM-DD"
            {...register("processing_date")}
            error={errors.processing_date?.message}
          />
        </div>
      </FormSection>

      {/* Merchant */}
      <FormSection title="Merchant Information">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Merchant ID"
            placeholder="123456789"
            maxLength={9}
            hint="Digits only, max 9 characters"
            {...register("merchant_id")}
            error={errors.merchant_id?.message}
          />
          <Input
            label="Merchant Name"
            placeholder="WHOLE FOODS MARKET"
            maxLength={50}
            {...register("merchant_name")}
            error={errors.merchant_name?.message}
          />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="City"
            placeholder="NEW YORK"
            maxLength={50}
            {...register("merchant_city")}
            error={errors.merchant_city?.message}
          />
          <Input
            label="ZIP Code"
            placeholder="10001"
            maxLength={10}
            {...register("merchant_zip")}
            error={errors.merchant_zip?.message}
          />
        </div>
      </FormSection>

      <div className="flex items-center gap-3">
        <Button type="submit" variant="primary">
          Review Transaction
        </Button>
        <Button type="button" variant="secondary" onClick={handleCopyLast}>
          Copy Last Transaction
        </Button>
        <Button type="button" variant="ghost" onClick={() => router.back()}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Confirm step — COBOL CONFIRM='Y' pattern
// ---------------------------------------------------------------------------

function ConfirmStep({
  values,
  onConfirm,
  onBack,
  isSubmitting,
}: {
  values: FormValues;
  onConfirm: () => void;
  onBack: () => void;
  isSubmitting: boolean;
}) {
  return (
    <div className="space-y-6">
      <Alert
        variant="warning"
        title="You are about to add this transaction"
        message="Please review the details below and confirm."
      />

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm divide-y divide-slate-100">
        <ConfirmRow label="Account ID" value={values.account_id || "—"} />
        <ConfirmRow label="Card Number" value={values.card_number || "—"} />
        <ConfirmRow label="Type / Category" value={`${values.type_code} / ${values.category_code}`} />
        <ConfirmRow label="Description" value={values.description} />
        <ConfirmRow label="Amount" value={`${values.amount}`} />
        <ConfirmRow label="Original Date" value={values.original_date} />
        <ConfirmRow label="Processing Date" value={values.processing_date} />
        <ConfirmRow label="Merchant" value={`${values.merchant_name} (${values.merchant_id})`} />
      </div>

      <div className="flex items-center gap-3">
        <Button onClick={onConfirm} disabled={isSubmitting} variant="primary">
          {isSubmitting ? "Submitting..." : "Confirm and Submit"}
        </Button>
        <Button variant="secondary" onClick={onBack} disabled={isSubmitting}>
          Go Back and Edit
        </Button>
      </div>
    </div>
  );
}

function ConfirmRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start gap-4 px-6 py-3">
      <dt className="w-36 flex-shrink-0 text-xs font-medium text-slate-500 uppercase tracking-wide pt-0.5">
        {label}
      </dt>
      <dd className="text-sm text-slate-900">{value || "—"}</dd>
    </div>
  );
}

function FormSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="bg-slate-50 px-6 py-3 border-b border-slate-200">
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">{title}</h2>
      </div>
      <div className="p-6 space-y-4">{children}</div>
    </div>
  );
}
