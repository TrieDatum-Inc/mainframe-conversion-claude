"use client";

import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import type { ReportRequest, ReportResponse } from "@/lib/types";
import { ApiError } from "@/lib/api";
import AlertMessage from "@/components/ui/AlertMessage";
import FormField from "@/components/ui/FormField";
import ConfirmDialog from "@/components/ui/ConfirmDialog";

const emptyForm: ReportRequest = {
  report_type: "monthly",
  start_month: undefined,
  start_day: undefined,
  start_year: undefined,
  end_month: undefined,
  end_day: undefined,
  end_year: undefined,
  confirm: "N",
};

export default function ReportForm() {
  const [form, setForm] = useState<ReportRequest>({ ...emptyForm });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState<Record<string, string>>({});
  const [previewMsg, setPreviewMsg] = useState("");
  const [showConfirm, setShowConfirm] = useState(false);
  const [result, setResult] = useState<ReportResponse | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFieldError((prev) => ({ ...prev, [name]: "" }));
    setForm((prev) => ({
      ...prev,
      [name]: ["start_month", "start_day", "start_year", "end_month", "end_day", "end_year"].includes(name)
        ? value === "" ? undefined : Number(value)
        : value,
    }));
  };

  const handlePreview = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    setFieldError({});
    setResult(null);

    try {
      const res = await api.post<ReportResponse>("/api/reports", { ...form, confirm: "N" });
      setPreviewMsg(res.message || "Report is ready to generate. Confirm to proceed.");
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
      const res = await api.post<ReportResponse>("/api/reports", { ...form, confirm: "Y" });
      setResult(res);
    } catch (err) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const isCustom = form.report_type === "custom";

  return (
    <div className="space-y-6">
      <form onSubmit={handlePreview} className="space-y-6">
        {error && <AlertMessage type="error" message={error} onDismiss={() => setError("")} />}

        <section className="rounded-lg border border-gray-200 bg-white">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
            <h3 className="text-sm font-semibold text-gray-700">Transaction Report</h3>
          </div>
          <div className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
            <FormField
              label="Report Type"
              name="report_type"
              value={form.report_type}
              onChange={handleChange}
              options={[
                { value: "monthly", label: "Monthly" },
                { value: "yearly", label: "Yearly" },
                { value: "custom", label: "Custom Date Range" },
              ]}
              error={fieldError.report_type}
            />
          </div>

          {isCustom && (
            <div className="border-t border-gray-200 p-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="mb-3 text-sm font-medium text-gray-700">Start Date</h4>
                  <div className="grid grid-cols-3 gap-2">
                    <FormField label="Month" name="start_month" type="number" value={form.start_month ?? ""} onChange={handleChange} placeholder="MM" error={fieldError.start_month} />
                    <FormField label="Day" name="start_day" type="number" value={form.start_day ?? ""} onChange={handleChange} placeholder="DD" error={fieldError.start_day} />
                    <FormField label="Year" name="start_year" type="number" value={form.start_year ?? ""} onChange={handleChange} placeholder="YYYY" error={fieldError.start_year} />
                  </div>
                </div>
                <div>
                  <h4 className="mb-3 text-sm font-medium text-gray-700">End Date</h4>
                  <div className="grid grid-cols-3 gap-2">
                    <FormField label="Month" name="end_month" type="number" value={form.end_month ?? ""} onChange={handleChange} placeholder="MM" error={fieldError.end_month} />
                    <FormField label="Day" name="end_day" type="number" value={form.end_day ?? ""} onChange={handleChange} placeholder="DD" error={fieldError.end_day} />
                    <FormField label="Year" name="end_year" type="number" value={form.end_year ?? ""} onChange={handleChange} placeholder="YYYY" error={fieldError.end_year} />
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700 disabled:opacity-50"
          >
            {submitting ? "Processing..." : "Preview Report"}
          </button>
        </div>
      </form>

      <ConfirmDialog
        open={showConfirm}
        title="Confirm Report Generation"
        onConfirm={handleConfirm}
        onCancel={() => setShowConfirm(false)}
        confirmLabel="Generate Report"
      >
        <p>{previewMsg}</p>
      </ConfirmDialog>

      {result && (
        <section className="rounded-lg border border-green-300 bg-green-50 p-6">
          <h3 className="text-lg font-semibold text-green-800">Report Generated</h3>
          <p className="mt-2 text-sm text-gray-700">{result.message}</p>
          {result.report_type && (
            <p className="mt-1 text-sm text-gray-600"><strong>Type:</strong> {result.report_type}</p>
          )}
        </section>
      )}
    </div>
  );
}
