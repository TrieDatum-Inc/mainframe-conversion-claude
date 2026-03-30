"use client";

import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import type { AuthDecisionRequest, AuthDecisionResponse } from "@/lib/types";
import { ApiError } from "@/lib/api";
import AlertMessage from "@/components/ui/AlertMessage";
import FormField from "@/components/ui/FormField";

export default function AuthDecisionForm() {
  const [form, setForm] = useState<AuthDecisionRequest>({
    card_num: "",
    auth_type: "",
    card_expiry_date: "",
    transaction_amt: 0,
    merchant_category_code: "",
    acqr_country_code: "",
    merchant_id: "",
    merchant_name: "",
    merchant_city: "",
    merchant_state: "",
    merchant_zip: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState<Record<string, string>>({});
  const [result, setResult] = useState<AuthDecisionResponse | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFieldError((prev) => ({ ...prev, [name]: "" }));
    setForm((prev) => ({
      ...prev,
      [name]: name === "transaction_amt" || name === "pos_entry_mode" ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    setFieldError({});
    setResult(null);

    try {
      // Strip empty strings from optional fields so the backend receives null instead of ""
      const payload: Record<string, unknown> = {
        card_num: form.card_num,
        auth_type: form.auth_type,
        card_expiry_date: form.card_expiry_date,
        transaction_amt: form.transaction_amt,
      };
      if (form.merchant_category_code) payload.merchant_category_code = form.merchant_category_code;
      if (form.acqr_country_code) payload.acqr_country_code = form.acqr_country_code;
      if (form.pos_entry_mode) payload.pos_entry_mode = form.pos_entry_mode;
      if (form.merchant_id) payload.merchant_id = form.merchant_id;
      if (form.merchant_name) payload.merchant_name = form.merchant_name;
      if (form.merchant_city) payload.merchant_city = form.merchant_city;
      if (form.merchant_state) payload.merchant_state = form.merchant_state;
      if (form.merchant_zip) payload.merchant_zip = form.merchant_zip;

      const res = await api.post<AuthDecisionResponse>("/api/authorizations/decide", payload);
      setResult(res);
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

  const isApproved = result?.auth_resp_code === "00";

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && <AlertMessage type="error" message={error} onDismiss={() => setError("")} />}

        <section className="rounded-lg border border-gray-200 bg-white">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
            <h3 className="text-sm font-semibold text-gray-700">Authorization Request</h3>
          </div>
          <div className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
            <FormField label="Card Number" name="card_num" value={form.card_num} onChange={handleChange} required error={fieldError.card_num} />
            <FormField label="Auth Type" name="auth_type" value={form.auth_type} onChange={handleChange} required error={fieldError.auth_type} />
            <FormField label="Card Expiry Date" name="card_expiry_date" value={form.card_expiry_date} onChange={handleChange} required placeholder="MMYY" error={fieldError.card_expiry_date} />
            <FormField label="Transaction Amount" name="transaction_amt" type="number" value={form.transaction_amt} onChange={handleChange} required error={fieldError.transaction_amt} />
            <FormField label="Merchant Category Code" name="merchant_category_code" value={form.merchant_category_code ?? ""} onChange={handleChange} />
            <FormField label="Acquirer Country Code" name="acqr_country_code" value={form.acqr_country_code ?? ""} onChange={handleChange} />
          </div>
        </section>

        <section className="rounded-lg border border-gray-200 bg-white">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
            <h3 className="text-sm font-semibold text-gray-700">Merchant Details (Optional)</h3>
          </div>
          <div className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2">
            <FormField label="Merchant ID" name="merchant_id" value={form.merchant_id ?? ""} onChange={handleChange} />
            <FormField label="Merchant Name" name="merchant_name" value={form.merchant_name ?? ""} onChange={handleChange} />
            <FormField label="City" name="merchant_city" value={form.merchant_city ?? ""} onChange={handleChange} />
            <FormField label="State" name="merchant_state" value={form.merchant_state ?? ""} onChange={handleChange} />
            <FormField label="ZIP" name="merchant_zip" value={form.merchant_zip ?? ""} onChange={handleChange} />
          </div>
        </section>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700 disabled:opacity-50"
          >
            {submitting ? "Processing..." : "Submit Authorization"}
          </button>
        </div>
      </form>

      {/* Result */}
      {result && (
        <section className={`rounded-lg border p-6 ${isApproved ? "border-green-300 bg-green-50" : "border-red-300 bg-red-50"}`}>
          <h3 className={`text-lg font-semibold ${isApproved ? "text-green-800" : "text-red-800"}`}>
            {isApproved ? "Authorization Approved" : "Authorization Declined"}
          </h3>
          <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <dt className="text-xs font-medium text-gray-500">Card Number</dt>
              <dd className="text-sm text-gray-900">{result.card_num}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">Transaction ID</dt>
              <dd className="text-sm text-gray-900">{result.transaction_id}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">Auth ID Code</dt>
              <dd className="text-sm text-gray-900">{result.auth_id_code}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">Response Code</dt>
              <dd className="text-sm text-gray-900">{result.auth_resp_code}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">Reason</dt>
              <dd className="text-sm text-gray-900">{result.auth_resp_reason}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">Approved Amount</dt>
              <dd className="text-sm text-gray-900">
                {new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(result.approved_amt)}
              </dd>
            </div>
          </dl>
        </section>
      )}
    </div>
  );
}
