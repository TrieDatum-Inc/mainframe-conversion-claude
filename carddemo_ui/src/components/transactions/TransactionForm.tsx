"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { TransactionCreate, MessageResponse } from "@/lib/types";
import { ApiError } from "@/lib/api";
import AlertMessage from "@/components/ui/AlertMessage";
import FormField from "@/components/ui/FormField";
import ConfirmDialog from "@/components/ui/ConfirmDialog";

const emptyForm: TransactionCreate = {
  card_num: "",
  tran_type_cd: "",
  tran_cat_cd: 0,
  tran_source: "",
  tran_desc: "",
  tran_amt: 0,
  tran_merchant_id: 0,
  tran_merchant_name: "",
  tran_merchant_city: "",
  tran_merchant_zip: "",
  confirm: "N",
};

export default function TransactionForm() {
  const router = useRouter();
  const [form, setForm] = useState<TransactionCreate>({ ...emptyForm });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState("");
  const [previewMsg, setPreviewMsg] = useState("");
  const [showConfirm, setShowConfirm] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFieldError((prev) => ({ ...prev, [name]: "" }));
    setForm((prev) => ({
      ...prev,
      [name]: ["tran_cat_cd", "tran_amt", "tran_merchant_id"].includes(name) ? Number(value) : value,
    }));
  };

  const handlePreview = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    setFieldError({});
    setSuccess("");

    try {
      const res = await api.post<MessageResponse>("/api/transactions", { ...form, confirm: "N" });
      setPreviewMsg(res.message || "Review the transaction details above, then confirm to submit.");
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
      const res = await api.post<MessageResponse>("/api/transactions", { ...form, confirm: "Y" });
      setSuccess(res.message || "Transaction created successfully.");
      setForm({ ...emptyForm });
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <form onSubmit={handlePreview} className="space-y-6">
        {error && <AlertMessage type="error" message={error} onDismiss={() => setError("")} />}
        {success && <AlertMessage type="success" message={success} onDismiss={() => setSuccess("")} />}

        <section className="rounded-lg border border-gray-200 bg-white">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
            <h3 className="text-sm font-semibold text-gray-700">Transaction Information</h3>
          </div>
          <div className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
            <FormField label="Card Number" name="card_num" value={form.card_num ?? ""} onChange={handleChange} required error={fieldError.card_num} />
            <FormField label="Type Code" name="tran_type_cd" value={form.tran_type_cd} onChange={handleChange} required error={fieldError.tran_type_cd} />
            <FormField label="Category Code" name="tran_cat_cd" type="number" value={form.tran_cat_cd} onChange={handleChange} required error={fieldError.tran_cat_cd} />
            <FormField label="Source" name="tran_source" value={form.tran_source} onChange={handleChange} required error={fieldError.tran_source} />
            <FormField label="Amount" name="tran_amt" type="number" value={form.tran_amt} onChange={handleChange} required error={fieldError.tran_amt} />
            <div className="sm:col-span-2 lg:col-span-3">
              <FormField label="Description" name="tran_desc" value={form.tran_desc} onChange={handleChange} required error={fieldError.tran_desc} />
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-gray-200 bg-white">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
            <h3 className="text-sm font-semibold text-gray-700">Merchant Information</h3>
          </div>
          <div className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2">
            <FormField label="Merchant ID" name="tran_merchant_id" type="number" value={form.tran_merchant_id} onChange={handleChange} required error={fieldError.tran_merchant_id} />
            <FormField label="Merchant Name" name="tran_merchant_name" value={form.tran_merchant_name} onChange={handleChange} required error={fieldError.tran_merchant_name} />
            <FormField label="City" name="tran_merchant_city" value={form.tran_merchant_city} onChange={handleChange} required error={fieldError.tran_merchant_city} />
            <FormField label="ZIP" name="tran_merchant_zip" value={form.tran_merchant_zip} onChange={handleChange} required error={fieldError.tran_merchant_zip} />
          </div>
        </section>

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => router.push("/transactions")}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700 disabled:opacity-50"
          >
            {submitting ? "Processing..." : "Preview"}
          </button>
        </div>
      </form>

      <ConfirmDialog
        open={showConfirm}
        title="Confirm Transaction"
        onConfirm={handleConfirm}
        onCancel={() => setShowConfirm(false)}
        confirmLabel="Submit Transaction"
      >
        <p>{previewMsg}</p>
        <div className="mt-3 rounded bg-gray-50 p-3 text-xs">
          <p><strong>Card:</strong> {form.card_num}</p>
          <p><strong>Amount:</strong> ${form.tran_amt}</p>
          <p><strong>Merchant:</strong> {form.tran_merchant_name}</p>
          <p><strong>Description:</strong> {form.tran_desc}</p>
        </div>
      </ConfirmDialog>
    </>
  );
}
