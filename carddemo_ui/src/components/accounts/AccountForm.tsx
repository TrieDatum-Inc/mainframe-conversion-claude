"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { AccountView, AccountUpdate, MessageResponse } from "@/lib/types";
import { ApiError } from "@/lib/api";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AlertMessage from "@/components/ui/AlertMessage";
import FormField from "@/components/ui/FormField";

interface AccountFormProps {
  acctId: string;
}

export default function AccountForm({ acctId }: AccountFormProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState("");
  const [form, setForm] = useState<AccountUpdate>({});

  useEffect(() => {
    if (!acctId) return;
    setLoading(true);
    api
      .get<AccountView>(`/api/accounts/${acctId}`)
      .then((data) => {
        setForm({
          acct_active_status: data.acct_active_status,
          acct_credit_limit: data.acct_credit_limit,
          acct_cash_credit_limit: data.acct_cash_credit_limit,
          acct_open_date: data.acct_open_date,
          acct_expiration_date: data.acct_expiration_date,
          acct_reissue_date: data.acct_reissue_date,
          cust_first_name: data.cust_first_name ?? "",
          cust_middle_name: data.cust_middle_name ?? "",
          cust_last_name: data.cust_last_name ?? "",
          cust_addr_line_1: data.cust_addr_line_1 ?? "",
          cust_addr_line_2: data.cust_addr_line_2 ?? "",
          cust_addr_line_3: data.cust_addr_line_3 ?? "",
          cust_addr_state_cd: data.cust_addr_state_cd ?? "",
          cust_addr_country_cd: data.cust_addr_country_cd ?? "",
          cust_addr_zip: data.cust_addr_zip ?? "",
          cust_phone_num_1: data.cust_phone_num_1 ?? "",
          cust_phone_num_2: data.cust_phone_num_2 ?? "",
          cust_ssn: data.cust_ssn,
          cust_govt_issued_id: data.cust_govt_issued_id ?? "",
          cust_dob_yyyymmdd: data.cust_dob_yyyymmdd ?? "",
          cust_eft_account_id: data.cust_eft_account_id ?? "",
          cust_pri_card_holder_ind: data.cust_pri_card_holder_ind ?? "N",
          cust_fico_credit_score: data.cust_fico_credit_score,
        });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [acctId]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFieldError((prev) => ({ ...prev, [name]: "" }));
    setForm((prev) => ({
      ...prev,
      [name]: ["acct_credit_limit", "acct_cash_credit_limit", "cust_ssn", "cust_fico_credit_score"].includes(name)
        ? value === "" ? undefined : Number(value)
        : value,
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    setFieldError({});

    try {
      const res = await api.put<MessageResponse>(`/api/accounts/${acctId}`, form);
      setSuccess(res.message || "Account updated successfully.");
    } catch (err) {
      if (err instanceof ApiError && err.field) {
        setFieldError({ [err.field]: err.message });
      } else if (err instanceof Error) {
        setError(err.message);
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error && !form.acct_active_status) return <AlertMessage type="error" message={error} />;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && <AlertMessage type="error" message={error} onDismiss={() => setError("")} />}
      {success && <AlertMessage type="success" message={success} onDismiss={() => setSuccess("")} />}

      {/* Account Fields */}
      <section className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
          <h3 className="text-sm font-semibold text-gray-700">Account Details</h3>
        </div>
        <div className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
          <FormField
            label="Status"
            name="acct_active_status"
            value={form.acct_active_status ?? ""}
            onChange={handleChange}
            options={[
              { value: "Y", label: "Active" },
              { value: "N", label: "Inactive" },
            ]}
            error={fieldError.acct_active_status}
          />
          <FormField
            label="Credit Limit"
            name="acct_credit_limit"
            type="number"
            value={form.acct_credit_limit ?? ""}
            onChange={handleChange}
            error={fieldError.acct_credit_limit}
          />
          <FormField
            label="Cash Credit Limit"
            name="acct_cash_credit_limit"
            type="number"
            value={form.acct_cash_credit_limit ?? ""}
            onChange={handleChange}
            error={fieldError.acct_cash_credit_limit}
          />
          <FormField
            label="Open Date"
            name="acct_open_date"
            value={form.acct_open_date ?? ""}
            onChange={handleChange}
            placeholder="YYYY-MM-DD"
            error={fieldError.acct_open_date}
          />
          <FormField
            label="Expiration Date"
            name="acct_expiration_date"
            value={form.acct_expiration_date ?? ""}
            onChange={handleChange}
            placeholder="YYYY-MM-DD"
            error={fieldError.acct_expiration_date}
          />
          <FormField
            label="Reissue Date"
            name="acct_reissue_date"
            value={form.acct_reissue_date ?? ""}
            onChange={handleChange}
            placeholder="YYYY-MM-DD"
            error={fieldError.acct_reissue_date}
          />
        </div>
      </section>

      {/* Customer Fields */}
      <section className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
          <h3 className="text-sm font-semibold text-gray-700">Customer Details</h3>
        </div>
        <div className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
          <FormField label="First Name" name="cust_first_name" value={form.cust_first_name ?? ""} onChange={handleChange} error={fieldError.cust_first_name} />
          <FormField label="Middle Name" name="cust_middle_name" value={form.cust_middle_name ?? ""} onChange={handleChange} />
          <FormField label="Last Name" name="cust_last_name" value={form.cust_last_name ?? ""} onChange={handleChange} error={fieldError.cust_last_name} />
          <FormField label="Address Line 1" name="cust_addr_line_1" value={form.cust_addr_line_1 ?? ""} onChange={handleChange} />
          <FormField label="Address Line 2" name="cust_addr_line_2" value={form.cust_addr_line_2 ?? ""} onChange={handleChange} />
          <FormField label="Address Line 3" name="cust_addr_line_3" value={form.cust_addr_line_3 ?? ""} onChange={handleChange} />
          <FormField label="State" name="cust_addr_state_cd" value={form.cust_addr_state_cd ?? ""} onChange={handleChange} />
          <FormField label="Country" name="cust_addr_country_cd" value={form.cust_addr_country_cd ?? ""} onChange={handleChange} />
          <FormField label="ZIP" name="cust_addr_zip" value={form.cust_addr_zip ?? ""} onChange={handleChange} />
          <FormField label="Phone 1" name="cust_phone_num_1" value={form.cust_phone_num_1 ?? ""} onChange={handleChange} />
          <FormField label="Phone 2" name="cust_phone_num_2" value={form.cust_phone_num_2 ?? ""} onChange={handleChange} />
          <FormField label="SSN" name="cust_ssn" type="number" value={form.cust_ssn ?? ""} onChange={handleChange} />
          <FormField label="Govt. Issued ID" name="cust_govt_issued_id" value={form.cust_govt_issued_id ?? ""} onChange={handleChange} />
          <FormField label="Date of Birth" name="cust_dob_yyyymmdd" value={form.cust_dob_yyyymmdd ?? ""} onChange={handleChange} placeholder="YYYYMMDD" />
          <FormField label="EFT Account" name="cust_eft_account_id" value={form.cust_eft_account_id ?? ""} onChange={handleChange} />
          <FormField
            label="Primary Card Holder"
            name="cust_pri_card_holder_ind"
            value={form.cust_pri_card_holder_ind ?? ""}
            onChange={handleChange}
            options={[
              { value: "Y", label: "Yes" },
              { value: "N", label: "No" },
            ]}
          />
          <FormField label="FICO Score" name="cust_fico_credit_score" type="number" value={form.cust_fico_credit_score ?? ""} onChange={handleChange} />
        </div>
      </section>

      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={() => router.push(`/accounts/${acctId}`)}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Changes"}
        </button>
      </div>
    </form>
  );
}
