"use client";

import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import type { BillPaymentRequest, BillPaymentResponse } from "@/lib/types";
import { ApiError } from "@/lib/api";
import AlertMessage from "@/components/ui/AlertMessage";
import FormField from "@/components/ui/FormField";
import ConfirmDialog from "@/components/ui/ConfirmDialog";

export default function BillPaymentForm() {
  const [acctId, setAcctId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState<Record<string, string>>({});
  const [previewData, setPreviewData] = useState<BillPaymentResponse | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [result, setResult] = useState<BillPaymentResponse | null>(null);

  const handlePreview = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    setFieldError({});
    setResult(null);

    try {
      const body: BillPaymentRequest = { acct_id: Number(acctId), confirm: "N" };
      const res = await api.post<BillPaymentResponse>("/api/bill-payment", body);
      setPreviewData(res);
      setShowConfirm(true);
    } catch (err) {
      if (err instanceof ApiError && err.field) {
        setFieldError({ [err.field]: err.message });
      } else if (err instanceof Error) {
        setError(err.message);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleConfirm = async () => {
    setShowConfirm(false);
    setSubmitting(true);
    setError("");

    try {
      const body: BillPaymentRequest = { acct_id: Number(acctId), confirm: "Y" };
      const res = await api.post<BillPaymentResponse>("/api/bill-payment", body);
      setResult(res);
    } catch (err) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const currency = (val: number) =>
    new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(val);

  return (
    <div className="space-y-6">
      <form onSubmit={handlePreview} className="space-y-6">
        {error && <AlertMessage type="error" message={error} onDismiss={() => setError("")} />}

        <section className="rounded-lg border border-gray-200 bg-white">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
            <h3 className="text-sm font-semibold text-gray-700">Bill Payment</h3>
          </div>
          <div className="p-6">
            <div className="max-w-sm">
              <FormField
                label="Account ID"
                name="acct_id"
                type="number"
                value={acctId}
                onChange={(e) => {
                  setAcctId(e.target.value);
                  setFieldError({});
                }}
                required
                error={fieldError.acct_id}
              />
            </div>
          </div>
        </section>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700 disabled:opacity-50"
          >
            {submitting ? "Processing..." : "Preview Payment"}
          </button>
        </div>
      </form>

      <ConfirmDialog
        open={showConfirm}
        title="Confirm Bill Payment"
        onConfirm={handleConfirm}
        onCancel={() => setShowConfirm(false)}
        confirmLabel="Pay Bill"
      >
        {previewData && (
          <div className="space-y-2">
            <p>{previewData.message}</p>
            {previewData.previous_balance != null && (
              <p><strong>Current Balance:</strong> {currency(previewData.previous_balance)}</p>
            )}
          </div>
        )}
      </ConfirmDialog>

      {/* Payment Result */}
      {result && (
        <section className="rounded-lg border border-green-300 bg-green-50 p-6">
          <h3 className="text-lg font-semibold text-green-800">Payment Successful</h3>
          <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <dt className="text-xs font-medium text-gray-500">Message</dt>
              <dd className="text-sm text-gray-900">{result.message}</dd>
            </div>
            {result.tran_id && (
              <div>
                <dt className="text-xs font-medium text-gray-500">Transaction ID</dt>
                <dd className="text-sm text-gray-900">{result.tran_id}</dd>
              </div>
            )}
            {result.previous_balance != null && (
              <div>
                <dt className="text-xs font-medium text-gray-500">Previous Balance</dt>
                <dd className="text-sm text-gray-900">{currency(result.previous_balance)}</dd>
              </div>
            )}
            {result.new_balance != null && (
              <div>
                <dt className="text-xs font-medium text-gray-500">New Balance</dt>
                <dd className="text-sm text-gray-900">{currency(result.new_balance)}</dd>
              </div>
            )}
          </dl>
        </section>
      )}
    </div>
  );
}
