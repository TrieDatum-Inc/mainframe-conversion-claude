"use client";

/**
 * AccountForm — editable account + customer form.
 *
 * Modernizes COACTUPC (4400-line COBOL program) screen:
 *   - All account fields editable (credit_limit, status, dates, group)
 *   - All customer fields editable (name, address, phone, SSN, FICO)
 *   - Client-side validation mirrors COACTUPC validation paragraphs
 *   - Phone: (xxx)xxx-xxxx format
 *   - SSN: xxx-xx-xxxx format
 *   - State code: 2-char from dropdown
 *   - Status: Y/N toggle (88-level condition equivalent)
 *
 * Account ID is display-only (key field — never editable, like ACCTSID PROT).
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { AccountDetail, AccountUpdateRequest } from "@/types";

// US state codes (mirrors CSLKPCDY table in COBOL)
const US_STATES = [
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
  "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
  "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
  "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
  "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
  "DC","PR","GU","VI","AS","MP",
];

interface AccountFormProps {
  account: AccountDetail;
  onSave: (payload: AccountUpdateRequest) => Promise<void>;
}

interface FormData {
  // Account fields
  active_status: string;
  credit_limit: string;
  cash_credit_limit: string;
  open_date: string;
  expiration_date: string;
  reissue_date: string;
  current_cycle_credit: string;
  current_cycle_debit: string;
  group_id: string;
  // Customer fields
  first_name: string;
  middle_name: string;
  last_name: string;
  address_line_1: string;
  address_line_2: string;
  address_line_3: string;
  state_code: string;
  country_code: string;
  zip_code: string;
  phone_1: string;
  phone_2: string;
  ssn: string;
  govt_issued_id: string;
  date_of_birth: string;
  eft_account_id: string;
  primary_card_holder: string;
  fico_score: string;
}

interface FormErrors {
  [key: string]: string;
}

// COBOL CSLKPCDY validation — phone format (xxx)xxx-xxxx
const PHONE_RE = /^\(\d{3}\)\d{3}-\d{4}$/;
// COBOL COACTUPC — SSN split fields ACTSSN1(3)+ACTSSN2(2)+ACTSSN3(4)
const SSN_RE = /^\d{3}-\d{2}-\d{4}$/;
// Zip: 5 digits or 5+4
const ZIP_RE = /^\d{5}(-\d{4})?$/;

function initFormData(account: AccountDetail): FormData {
  const c = account.customer;
  const toDateStr = (v: string | null) => (v ? v.substring(0, 10) : "");
  return {
    active_status: account.active_status,
    credit_limit: String(account.credit_limit),
    cash_credit_limit: String(account.cash_credit_limit),
    open_date: toDateStr(account.open_date),
    expiration_date: toDateStr(account.expiration_date),
    reissue_date: toDateStr(account.reissue_date),
    current_cycle_credit: String(account.current_cycle_credit),
    current_cycle_debit: String(account.current_cycle_debit),
    group_id: account.group_id ?? "",
    first_name: c?.first_name ?? "",
    middle_name: c?.middle_name ?? "",
    last_name: c?.last_name ?? "",
    address_line_1: c?.address_line_1 ?? "",
    address_line_2: c?.address_line_2 ?? "",
    address_line_3: c?.address_line_3 ?? "",
    state_code: c?.state_code ?? "",
    country_code: c?.country_code ?? "USA",
    zip_code: c?.zip_code ?? "",
    phone_1: c?.phone_1 ?? "",
    phone_2: c?.phone_2 ?? "",
    ssn: c?.ssn ?? "",
    govt_issued_id: c?.govt_issued_id ?? "",
    date_of_birth: toDateStr(c?.date_of_birth ?? null),
    eft_account_id: c?.eft_account_id ?? "",
    primary_card_holder: c?.primary_card_holder ?? "Y",
    fico_score: c?.fico_score !== null && c?.fico_score !== undefined ? String(c.fico_score) : "",
  };
}

function validateForm(data: FormData): FormErrors {
  const errors: FormErrors = {};

  if (!["Y", "N"].includes(data.active_status)) {
    errors.active_status = "Status must be Y or N";
  }

  if (data.phone_1 && !PHONE_RE.test(data.phone_1)) {
    errors.phone_1 = "Format: (xxx)xxx-xxxx";
  }
  if (data.phone_2 && !PHONE_RE.test(data.phone_2)) {
    errors.phone_2 = "Format: (xxx)xxx-xxxx";
  }
  if (data.ssn && !SSN_RE.test(data.ssn)) {
    errors.ssn = "Format: xxx-xx-xxxx";
  }
  if (data.zip_code && !ZIP_RE.test(data.zip_code)) {
    errors.zip_code = "Format: 12345 or 12345-6789";
  }
  if (data.state_code && !US_STATES.includes(data.state_code.toUpperCase())) {
    errors.state_code = "Invalid state code";
  }
  if (data.fico_score) {
    const score = parseInt(data.fico_score, 10);
    if (isNaN(score) || score < 300 || score > 850) {
      errors.fico_score = "FICO score must be 300–850";
    }
  }
  if (data.credit_limit && isNaN(parseFloat(data.credit_limit))) {
    errors.credit_limit = "Must be a number";
  }
  if (data.cash_credit_limit && isNaN(parseFloat(data.cash_credit_limit))) {
    errors.cash_credit_limit = "Must be a number";
  }

  return errors;
}

function buildPayload(data: FormData): AccountUpdateRequest {
  const payload: AccountUpdateRequest = {
    active_status: data.active_status,
    group_id: data.group_id || null,
  };

  if (data.credit_limit) payload.credit_limit = parseFloat(data.credit_limit);
  if (data.cash_credit_limit) payload.cash_credit_limit = parseFloat(data.cash_credit_limit);
  if (data.open_date) payload.open_date = data.open_date;
  if (data.expiration_date) payload.expiration_date = data.expiration_date;
  if (data.reissue_date) payload.reissue_date = data.reissue_date;
  if (data.current_cycle_credit) payload.current_cycle_credit = parseFloat(data.current_cycle_credit);
  if (data.current_cycle_debit) payload.current_cycle_debit = parseFloat(data.current_cycle_debit);
  if (data.first_name) payload.first_name = data.first_name;
  if (data.middle_name !== undefined) payload.middle_name = data.middle_name;
  if (data.last_name) payload.last_name = data.last_name;
  if (data.address_line_1 !== undefined) payload.address_line_1 = data.address_line_1;
  if (data.address_line_2 !== undefined) payload.address_line_2 = data.address_line_2;
  if (data.address_line_3 !== undefined) payload.address_line_3 = data.address_line_3;
  if (data.state_code) payload.state_code = data.state_code.toUpperCase();
  if (data.country_code) payload.country_code = data.country_code;
  if (data.zip_code) payload.zip_code = data.zip_code;
  if (data.phone_1 !== undefined) payload.phone_1 = data.phone_1;
  if (data.phone_2 !== undefined) payload.phone_2 = data.phone_2;
  if (data.ssn) payload.ssn = data.ssn;
  if (data.govt_issued_id !== undefined) payload.govt_issued_id = data.govt_issued_id;
  if (data.date_of_birth) payload.date_of_birth = data.date_of_birth;
  if (data.eft_account_id !== undefined) payload.eft_account_id = data.eft_account_id;
  if (data.primary_card_holder) payload.primary_card_holder = data.primary_card_holder;
  if (data.fico_score) payload.fico_score = parseInt(data.fico_score, 10);

  return payload;
}

function FormSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-200 px-6 py-4">
        <h2 className="text-base font-semibold text-gray-900">{title}</h2>
      </div>
      <div className="grid grid-cols-1 gap-4 px-6 py-4 sm:grid-cols-2">{children}</div>
    </div>
  );
}

function Field({
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
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <div className="mt-1">{children}</div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}

const inputCls =
  "block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500";

const readonlyCls =
  "block w-full rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-600";

export function AccountForm({ account, onSave }: AccountFormProps) {
  const router = useRouter();
  const [formData, setFormData] = useState<FormData>(() => initFormData(account));
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const update = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
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
      router.push(`/accounts/${account.account_id}`);
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
          <h1 className="text-2xl font-bold text-gray-900">
            Edit Account
          </h1>
          <p className="text-sm text-gray-500 font-mono mt-1">
            Account ID: {account.account_id}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => router.push(`/accounts/${account.account_id}`)}
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
      </div>

      {saveError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {saveError}
        </div>
      )}

      {/* Account Fields */}
      <FormSection title="Account Information">
        <Field label="Account ID">
          <input className={readonlyCls} value={account.account_id} readOnly />
        </Field>
        <Field label="Active Status" error={errors.active_status}>
          <select
            className={inputCls}
            value={formData.active_status}
            onChange={(e) => update("active_status", e.target.value)}
          >
            <option value="Y">Y — Active</option>
            <option value="N">N — Inactive</option>
          </select>
        </Field>
        <Field label="Credit Limit" error={errors.credit_limit}>
          <input
            className={inputCls}
            type="number"
            step="0.01"
            min="0"
            value={formData.credit_limit}
            onChange={(e) => update("credit_limit", e.target.value)}
          />
        </Field>
        <Field label="Cash Credit Limit" error={errors.cash_credit_limit}>
          <input
            className={inputCls}
            type="number"
            step="0.01"
            min="0"
            value={formData.cash_credit_limit}
            onChange={(e) => update("cash_credit_limit", e.target.value)}
          />
        </Field>
        <Field label="Open Date">
          <input
            className={inputCls}
            type="date"
            value={formData.open_date}
            onChange={(e) => update("open_date", e.target.value)}
          />
        </Field>
        <Field label="Expiration Date">
          <input
            className={inputCls}
            type="date"
            value={formData.expiration_date}
            onChange={(e) => update("expiration_date", e.target.value)}
          />
        </Field>
        <Field label="Reissue Date">
          <input
            className={inputCls}
            type="date"
            value={formData.reissue_date}
            onChange={(e) => update("reissue_date", e.target.value)}
          />
        </Field>
        <Field label="Group ID">
          <input
            className={inputCls}
            maxLength={10}
            value={formData.group_id}
            onChange={(e) => update("group_id", e.target.value)}
          />
        </Field>
        <Field label="Current Cycle Credit" error={errors.current_cycle_credit}>
          <input
            className={inputCls}
            type="number"
            step="0.01"
            value={formData.current_cycle_credit}
            onChange={(e) => update("current_cycle_credit", e.target.value)}
          />
        </Field>
        <Field label="Current Cycle Debit" error={errors.current_cycle_debit}>
          <input
            className={inputCls}
            type="number"
            step="0.01"
            value={formData.current_cycle_debit}
            onChange={(e) => update("current_cycle_debit", e.target.value)}
          />
        </Field>
      </FormSection>

      {/* Customer Fields */}
      <FormSection title="Customer Information">
        <Field label="First Name">
          <input
            className={inputCls}
            maxLength={25}
            value={formData.first_name}
            onChange={(e) => update("first_name", e.target.value)}
          />
        </Field>
        <Field label="Middle Name">
          <input
            className={inputCls}
            maxLength={25}
            value={formData.middle_name}
            onChange={(e) => update("middle_name", e.target.value)}
          />
        </Field>
        <Field label="Last Name">
          <input
            className={inputCls}
            maxLength={25}
            value={formData.last_name}
            onChange={(e) => update("last_name", e.target.value)}
          />
        </Field>
        <Field label="Address Line 1">
          <input
            className={inputCls}
            maxLength={50}
            value={formData.address_line_1}
            onChange={(e) => update("address_line_1", e.target.value)}
          />
        </Field>
        <Field label="Address Line 2">
          <input
            className={inputCls}
            maxLength={50}
            value={formData.address_line_2}
            onChange={(e) => update("address_line_2", e.target.value)}
          />
        </Field>
        <Field label="Address Line 3">
          <input
            className={inputCls}
            maxLength={50}
            value={formData.address_line_3}
            onChange={(e) => update("address_line_3", e.target.value)}
          />
        </Field>
        <Field label="State Code" error={errors.state_code}>
          <select
            className={inputCls}
            value={formData.state_code}
            onChange={(e) => update("state_code", e.target.value)}
          >
            <option value="">Select state...</option>
            {US_STATES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </Field>
        <Field label="Zip Code" error={errors.zip_code}>
          <input
            className={inputCls}
            maxLength={10}
            placeholder="12345 or 12345-6789"
            value={formData.zip_code}
            onChange={(e) => update("zip_code", e.target.value)}
          />
        </Field>
        <Field label="Country Code">
          <input
            className={inputCls}
            maxLength={3}
            value={formData.country_code}
            onChange={(e) => update("country_code", e.target.value)}
          />
        </Field>
        <Field label="Phone 1" error={errors.phone_1}>
          <input
            className={inputCls}
            maxLength={15}
            placeholder="(214)555-1234"
            value={formData.phone_1}
            onChange={(e) => update("phone_1", e.target.value)}
          />
        </Field>
        <Field label="Phone 2" error={errors.phone_2}>
          <input
            className={inputCls}
            maxLength={15}
            placeholder="(214)555-5678"
            value={formData.phone_2}
            onChange={(e) => update("phone_2", e.target.value)}
          />
        </Field>
        <Field label="SSN" error={errors.ssn}>
          <input
            className={inputCls}
            maxLength={11}
            placeholder="xxx-xx-xxxx"
            value={formData.ssn}
            onChange={(e) => update("ssn", e.target.value)}
          />
        </Field>
        <Field label="Date of Birth">
          <input
            className={inputCls}
            type="date"
            value={formData.date_of_birth}
            onChange={(e) => update("date_of_birth", e.target.value)}
          />
        </Field>
        <Field label="FICO Score" error={errors.fico_score}>
          <input
            className={inputCls}
            type="number"
            min="300"
            max="850"
            value={formData.fico_score}
            onChange={(e) => update("fico_score", e.target.value)}
          />
        </Field>
        <Field label="Government ID">
          <input
            className={inputCls}
            maxLength={20}
            value={formData.govt_issued_id}
            onChange={(e) => update("govt_issued_id", e.target.value)}
          />
        </Field>
        <Field label="EFT Account ID">
          <input
            className={inputCls}
            maxLength={10}
            value={formData.eft_account_id}
            onChange={(e) => update("eft_account_id", e.target.value)}
          />
        </Field>
        <Field label="Primary Card Holder">
          <select
            className={inputCls}
            value={formData.primary_card_holder}
            onChange={(e) => update("primary_card_holder", e.target.value)}
          >
            <option value="Y">Y — Yes</option>
            <option value="N">N — No</option>
          </select>
        </Field>
      </FormSection>

      {/* Bottom buttons */}
      <div className="flex justify-end gap-2 pb-8">
        <button
          type="button"
          onClick={() => router.push(`/accounts/${account.account_id}`)}
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
