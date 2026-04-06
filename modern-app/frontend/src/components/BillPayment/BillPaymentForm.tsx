"use client";

/**
 * BillPaymentForm — modern form replacing COBIL00C BMS screen.
 *
 * COBOL flow:
 *   1. Enter Account ID (ACTIDIN) → lookup balance (CURBAL)
 *   2. Display balance, prompt Y/N (CONFIRM)
 *   3. CONFIRM='Y' → write payment transaction, zero balance
 *
 * Business rules preserved:
 *   - Payment is ALWAYS for the full current balance (no partial)
 *   - If balance <= 0 → "You have nothing to pay"
 *   - Transaction type='02', merchant_id='999999999'
 */

import { useState } from "react";
import { previewBillPayment, processBillPayment } from "@/lib/api";
import { formatAmount, getErrorMessage } from "@/lib/utils";
import type { BillPaymentPreview, BillPaymentResult } from "@/types";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";

type Step = "input" | "preview" | "success";

export function BillPaymentForm() {
  const [step, setStep] = useState<Step>("input");
  const [accountId, setAccountId] = useState("");
  const [accountIdError, setAccountIdError] = useState("");
  const [preview, setPreview] = useState<BillPaymentPreview | null>(null);
  const [result, setResult] = useState<BillPaymentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleLookup() {
    if (!accountId.trim()) {
      setAccountIdError("Account ID is required");
      return;
    }
    setAccountIdError("");
    setError(null);
    setIsLoading(true);
    try {
      const data = await previewBillPayment(accountId.trim());
      setPreview(data);
      setStep("preview");
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleConfirm() {
    setError(null);
    setIsLoading(true);
    try {
      const data = await processBillPayment({ account_id: accountId.trim(), confirmed: true });
      setResult(data);
      setStep("success");
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setIsLoading(false);
    }
  }

  function handleReset() {
    setStep("input");
    setAccountId("");
    setPreview(null);
    setResult(null);
    setError(null);
  }

  return (
    <div className="max-w-lg space-y-6">
      {error && <Alert variant="error" message={error} />}

      {step === "input" && (
        <InputStep
          accountId={accountId}
          accountIdError={accountIdError}
          isLoading={isLoading}
          onAccountIdChange={setAccountId}
          onLookup={handleLookup}
        />
      )}

      {step === "preview" && preview && (
        <PreviewStep
          preview={preview}
          isLoading={isLoading}
          onConfirm={handleConfirm}
          onBack={() => setStep("input")}
        />
      )}

      {step === "success" && result && (
        <SuccessStep result={result} onReset={handleReset} />
      )}
    </div>
  );
}

function InputStep({
  accountId,
  accountIdError,
  isLoading,
  onAccountIdChange,
  onLookup,
}: {
  accountId: string;
  accountIdError: string;
  isLoading: boolean;
  onAccountIdChange: (v: string) => void;
  onLookup: () => void;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-6 space-y-4">
      <h2 className="text-lg font-semibold text-slate-900">Enter Account ID</h2>
      <Input
        label="Account ID"
        placeholder="00000001000"
        maxLength={11}
        value={accountId}
        onChange={(e) => onAccountIdChange(e.target.value)}
        error={accountIdError}
        onKeyDown={(e) => e.key === "Enter" && onLookup()}
        autoFocus
      />
      <Button onClick={onLookup} disabled={isLoading}>
        {isLoading ? "Looking up..." : "Look Up Balance"}
      </Button>
    </div>
  );
}

function PreviewStep({
  preview,
  isLoading,
  onConfirm,
  onBack,
}: {
  preview: BillPaymentPreview;
  isLoading: boolean;
  onConfirm: () => void;
  onBack: () => void;
}) {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Current Balance</h2>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600">Account {preview.account_id}</span>
          <span
            className={`text-2xl font-bold ${
              preview.current_balance > 0 ? "text-red-600" : "text-green-600"
            }`}
          >
            {formatAmount(preview.current_balance)}
          </span>
        </div>
      </div>

      {!preview.can_pay ? (
        <Alert variant="info" message={preview.message} />
      ) : (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 space-y-4">
          <p className="text-sm text-amber-800 font-medium">
            Your full balance of{" "}
            <span className="font-bold">{formatAmount(preview.current_balance)}</span> will be
            paid. This cannot be undone.
          </p>
          <div className="flex items-center gap-3">
            <Button onClick={onConfirm} disabled={isLoading} variant="primary">
              {isLoading ? "Processing..." : "Confirm Payment"}
            </Button>
            <Button variant="secondary" onClick={onBack} disabled={isLoading}>
              Cancel
            </Button>
          </div>
        </div>
      )}

      {preview.can_pay && (
        <Button variant="ghost" onClick={onBack} disabled={isLoading} className="text-sm">
          Change Account
        </Button>
      )}
    </div>
  );
}

function SuccessStep({
  result,
  onReset,
}: {
  result: BillPaymentResult;
  onReset: () => void;
}) {
  return (
    <div className="space-y-4">
      <Alert variant="success" title="Payment Successful" message={result.message} />
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm divide-y divide-slate-100">
        <PayRow label="Account ID" value={result.account_id} />
        <PayRow label="Card Number" value={result.card_number} />
        <PayRow label="Transaction ID" value={result.transaction_id} mono />
        <PayRow label="Amount Paid" value={formatAmount(result.amount_paid)} />
        <PayRow label="New Balance" value={formatAmount(result.new_balance)} />
      </div>
      <Button onClick={onReset} variant="secondary">
        Make Another Payment
      </Button>
    </div>
  );
}

function PayRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between px-6 py-3">
      <dt className="text-sm text-slate-500">{label}</dt>
      <dd className={`text-sm font-medium text-slate-900 ${mono ? "font-mono" : ""}`}>{value}</dd>
    </div>
  );
}
