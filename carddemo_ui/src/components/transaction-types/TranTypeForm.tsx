"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { TransactionTypeCreate, MessageResponse } from "@/lib/types";
import { ApiError } from "@/lib/api";
import AlertMessage from "@/components/ui/AlertMessage";
import FormField from "@/components/ui/FormField";

export default function TranTypeForm() {
  const router = useRouter();
  const [form, setForm] = useState<TransactionTypeCreate>({
    tran_type: "",
    tran_type_desc: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState<Record<string, string>>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFieldError((prev) => ({ ...prev, [name]: "" }));
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setFieldError({});

    try {
      await api.post<MessageResponse>("/api/transaction-types", form);
      router.push("/admin/transaction-types");
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

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && <AlertMessage type="error" message={error} onDismiss={() => setError("")} />}

      <section className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
          <h3 className="text-sm font-semibold text-gray-700">Add Transaction Type</h3>
        </div>
        <div className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2">
          <FormField
            label="Type Code"
            name="tran_type"
            value={form.tran_type}
            onChange={handleChange}
            required
            error={fieldError.tran_type}
            placeholder="e.g., SA"
          />
          <FormField
            label="Description"
            name="tran_type_desc"
            value={form.tran_type_desc}
            onChange={handleChange}
            required
            error={fieldError.tran_type_desc}
            placeholder="e.g., Sale"
          />
        </div>
      </section>

      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={() => router.push("/admin/transaction-types")}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700 disabled:opacity-50"
        >
          {saving ? "Creating..." : "Create Type"}
        </button>
      </div>
    </form>
  );
}
