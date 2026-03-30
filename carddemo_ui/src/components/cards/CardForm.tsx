"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { CardDetail, CardUpdate, MessageResponse } from "@/lib/types";
import { ApiError } from "@/lib/api";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AlertMessage from "@/components/ui/AlertMessage";
import FormField from "@/components/ui/FormField";

interface CardFormProps {
  cardNum: string;
}

export default function CardForm({ cardNum }: CardFormProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState("");
  const [form, setForm] = useState<CardUpdate>({});
  const [acctId, setAcctId] = useState<number | null>(null);

  useEffect(() => {
    if (!cardNum) return;
    setLoading(true);
    api
      .get<CardDetail>(`/api/cards/${cardNum}`)
      .then((data) => {
        setAcctId(data.card_acct_id);
        setForm({
          card_embossed_name: data.card_embossed_name,
          card_active_status: data.card_active_status,
          card_expiration_date: data.card_expiration_date,
        });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [cardNum]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFieldError((prev) => ({ ...prev, [name]: "" }));
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    setFieldError({});

    try {
      const res = await api.put<MessageResponse>(`/api/cards/${cardNum}?acct_id=${acctId}`, form);
      setSuccess(res.message || "Card updated successfully.");
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
  if (error && !form.card_embossed_name) return <AlertMessage type="error" message={error} />;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && <AlertMessage type="error" message={error} onDismiss={() => setError("")} />}
      {success && <AlertMessage type="success" message={success} onDismiss={() => setSuccess("")} />}

      <section className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
          <h3 className="text-sm font-semibold text-gray-700">Edit Card: {cardNum}</h3>
        </div>
        <div className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2">
          <FormField
            label="Embossed Name"
            name="card_embossed_name"
            value={form.card_embossed_name ?? ""}
            onChange={handleChange}
            required
            error={fieldError.card_embossed_name}
          />
          <FormField
            label="Status"
            name="card_active_status"
            value={form.card_active_status ?? ""}
            onChange={handleChange}
            options={[
              { value: "Y", label: "Active" },
              { value: "N", label: "Inactive" },
            ]}
            error={fieldError.card_active_status}
          />
          <FormField
            label="Expiration Date"
            name="card_expiration_date"
            value={form.card_expiration_date ?? ""}
            onChange={handleChange}
            placeholder="YYYY-MM-DD"
            error={fieldError.card_expiration_date}
          />
        </div>
      </section>

      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={() => router.push(`/cards/${cardNum}`)}
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
