"use client";

/**
 * CardForm — credit card update form.
 *
 * Modernizes COCRDUPC screen:
 *   - Account number: PROTECTED (display only — ACCTSID PROT in BMS)
 *   - Editable: embossed_name (CRDNAME), active_status (CRDSTCD Y/N),
 *               expiry month (EXPMON 1-12), expiry year (EXPYEAR 1950-2099)
 *   - Card number shown but not editable (CARDSID — cannot change card number)
 *
 * Validation mirrors COCRDUPC inline rules:
 *   - Name non-blank (CRDNAME non-blank alphanumeric)
 *   - Status Y or N (88-level FLG-YES-NO-VALID)
 *   - Month 1-12 (VALID-MONTH VALUE 1 THRU 12)
 *   - Year 1950-2099 (VALID-YEAR VALUE 1950 THRU 2099)
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { CardDetail, CardUpdateRequest } from "@/types";

interface CardFormProps {
  card: CardDetail;
  onSave: (payload: CardUpdateRequest) => Promise<void>;
}

interface FormData {
  embossed_name: string;
  active_status: string;
  expiry_month: string;
  expiry_year: string;
}

interface FormErrors {
  embossed_name?: string;
  active_status?: string;
  expiry_month?: string;
  expiry_year?: string;
}

function initFormData(card: CardDetail): FormData {
  let expMonth = "";
  let expYear = "";
  if (card.expiration_date) {
    const d = new Date(card.expiration_date);
    expMonth = String(d.getMonth() + 1);
    expYear = String(d.getFullYear());
  }
  return {
    embossed_name: card.embossed_name,
    active_status: card.active_status,
    expiry_month: expMonth,
    expiry_year: expYear,
  };
}

function validateForm(data: FormData): FormErrors {
  const errors: FormErrors = {};

  // COBOL: CRDNAME must be non-blank
  if (!data.embossed_name.trim()) {
    errors.embossed_name = "Name on card must not be blank";
  }

  // COBOL: 88-level FLG-YES-NO-VALID VALUE 'Y' 'N'
  if (!["Y", "N"].includes(data.active_status)) {
    errors.active_status = "Status must be Y or N";
  }

  // COBOL: VALID-MONTH VALUE 1 THRU 12
  if (data.expiry_month) {
    const m = parseInt(data.expiry_month, 10);
    if (isNaN(m) || m < 1 || m > 12) {
      errors.expiry_month = "Month must be 1–12";
    }
  }

  // COBOL: VALID-YEAR VALUE 1950 THRU 2099
  if (data.expiry_year) {
    const y = parseInt(data.expiry_year, 10);
    if (isNaN(y) || y < 1950 || y > 2099) {
      errors.expiry_year = "Year must be 1950–2099";
    }
  }

  return errors;
}

function buildPayload(data: FormData): CardUpdateRequest {
  const payload: CardUpdateRequest = {
    embossed_name: data.embossed_name,
    active_status: data.active_status,
  };
  if (data.expiry_month) payload.expiry_month = parseInt(data.expiry_month, 10);
  if (data.expiry_year) payload.expiry_year = parseInt(data.expiry_year, 10);
  return payload;
}

const inputCls =
  "block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500";

const readonlyCls =
  "block w-full rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-600 cursor-not-allowed";

function Field({
  label,
  error,
  required,
  children,
}: {
  label: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="ml-1 text-red-500">*</span>}
      </label>
      <div className="mt-1">{children}</div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}

export function CardForm({ card, onSave }: CardFormProps) {
  const router = useRouter();
  const [formData, setFormData] = useState<FormData>(() => initFormData(card));
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const update = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationErrors = validateForm(formData);
    if (Object.values(validationErrors).some(Boolean)) {
      setErrors(validationErrors);
      return;
    }

    setIsSaving(true);
    setSaveError(null);
    try {
      await onSave(buildPayload(formData));
      router.push(`/cards/${card.card_number}`);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Edit Card</h1>
          <p className="mt-1 text-sm font-mono text-gray-500">{card.card_number}</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => router.push(`/cards/${card.card_number}`)}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel (F12)
          </button>
          <button
            type="submit"
            disabled={isSaving}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {isSaving ? "Saving..." : "Save (F5)"}
          </button>
        </div>
      </div>

      {saveError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {saveError}
        </div>
      )}

      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-base font-semibold text-gray-900">Card Details</h2>
        </div>
        <div className="grid grid-cols-1 gap-6 px-6 py-6 sm:grid-cols-2">

          {/* PROTECTED fields (read-only) */}
          <Field label="Account Number">
            <div className="relative">
              <input
                className={readonlyCls}
                value={card.account_id}
                readOnly
                aria-readonly="true"
              />
              <span className="absolute right-2 top-2 text-xs text-gray-400">
                Protected
              </span>
            </div>
          </Field>

          <Field label="Card Number">
            <input className={readonlyCls} value={card.card_number} readOnly />
          </Field>

          {/* EDITABLE fields */}
          <Field label="Name on Card" error={errors.embossed_name} required>
            <input
              className={inputCls}
              maxLength={50}
              value={formData.embossed_name}
              onChange={(e) => update("embossed_name", e.target.value)}
              placeholder="Full name as embossed"
            />
          </Field>

          <Field label="Active Status" error={errors.active_status} required>
            <select
              className={inputCls}
              value={formData.active_status}
              onChange={(e) => update("active_status", e.target.value)}
            >
              <option value="Y">Y — Active</option>
              <option value="N">N — Inactive</option>
            </select>
          </Field>

          <Field
            label="Expiry Month (1–12)"
            error={errors.expiry_month}
            required
          >
            <select
              className={inputCls}
              value={formData.expiry_month}
              onChange={(e) => update("expiry_month", e.target.value)}
            >
              <option value="">Select month...</option>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={String(m)}>
                  {String(m).padStart(2, "0")} — {new Date(2000, m - 1).toLocaleString("en-US", { month: "long" })}
                </option>
              ))}
            </select>
          </Field>

          <Field
            label="Expiry Year (1950–2099)"
            error={errors.expiry_year}
            required
          >
            <input
              className={inputCls}
              type="number"
              min="1950"
              max="2099"
              value={formData.expiry_year}
              onChange={(e) => update("expiry_year", e.target.value)}
              placeholder="YYYY"
            />
          </Field>
        </div>
      </div>

      {/* Note about protected field */}
      <p className="text-xs text-gray-400">
        Fields marked "Protected" cannot be modified (mirrors COCRDUPC ACCTSID PROT attribute).
      </p>

      <div className="flex justify-end gap-2 pb-8">
        <button
          type="button"
          onClick={() => router.push(`/cards/${card.card_number}`)}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSaving}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {isSaving ? "Saving..." : "Save Changes"}
        </button>
      </div>
    </form>
  );
}
