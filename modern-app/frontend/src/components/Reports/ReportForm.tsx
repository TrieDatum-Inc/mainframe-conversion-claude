"use client";

/**
 * ReportForm — modern form replacing CORPT00C BMS report screen.
 *
 * COBOL BMS fields → UI:
 *   MONTHLY  → radio button (current month)
 *   YEARLY   → radio button (current year Jan–Dec)
 *   CUSTOM   → radio button + date pickers
 *   CONFIRM  → Confirm and Generate button (CONFIRM='Y')
 *
 * Results are displayed in a table; CSV download is also offered.
 */

import { useState } from "react";
import { generateReport } from "@/lib/api";
import { formatAmount, getErrorMessage, amountColorClass } from "@/lib/utils";
import type { ReportResult, ReportType } from "@/types";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";

export function ReportForm() {
  const [reportType, setReportType] = useState<ReportType>("monthly");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [result, setResult] = useState<ReportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState<"form" | "confirm">("form");

  function handleSubmitForm() {
    setError(null);
    if (reportType === "custom") {
      if (!startDate || !endDate) {
        setError("Start date and end date are required for custom reports");
        return;
      }
      if (endDate < startDate) {
        setError("End date must be on or after start date");
        return;
      }
    }
    setStep("confirm");
  }

  async function handleConfirm() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await generateReport({
        report_type: reportType,
        start_date: reportType === "custom" ? startDate : undefined,
        end_date: reportType === "custom" ? endDate : undefined,
        confirmed: true,
      });
      setResult(data);
      setStep("form");
    } catch (e) {
      setError(getErrorMessage(e));
      setStep("form");
    } finally {
      setIsLoading(false);
    }
  }

  function downloadCsv() {
    if (!result) return;
    const header = "transaction_id,card_number,type_code,category_code,description,amount,original_date,processing_date,merchant_name,merchant_city\n";
    const rows = result.transactions
      .map((t) =>
        [
          t.transaction_id, t.card_number, t.type_code, t.category_code,
          `"${t.description}"`, t.amount, t.original_date, t.processing_date,
          `"${t.merchant_name}"`, t.merchant_city,
        ].join(",")
      )
      .join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `transactions_${result.start_date}_${result.end_date}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      {error && <Alert variant="error" message={error} />}

      {step === "confirm" ? (
        <ConfirmStep
          reportType={reportType}
          startDate={startDate}
          endDate={endDate}
          isLoading={isLoading}
          onConfirm={handleConfirm}
          onBack={() => setStep("form")}
        />
      ) : (
        <FormStep
          reportType={reportType}
          startDate={startDate}
          endDate={endDate}
          onReportTypeChange={setReportType}
          onStartDateChange={setStartDate}
          onEndDateChange={setEndDate}
          onSubmit={handleSubmitForm}
        />
      )}

      {result && <ReportResults result={result} onDownloadCsv={downloadCsv} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function FormStep({
  reportType, startDate, endDate,
  onReportTypeChange, onStartDateChange, onEndDateChange, onSubmit,
}: {
  reportType: ReportType;
  startDate: string;
  endDate: string;
  onReportTypeChange: (t: ReportType) => void;
  onStartDateChange: (v: string) => void;
  onEndDateChange: (v: string) => void;
  onSubmit: () => void;
}) {
  const reportOptions: { value: ReportType; label: string; description: string }[] = [
    { value: "monthly", label: "Monthly", description: "Current month (first to last day)" },
    { value: "yearly", label: "Yearly", description: "Jan 1 to Dec 31 of current year" },
    { value: "custom", label: "Custom Date Range", description: "Choose your own start and end dates" },
  ];

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-6 space-y-6">
      <h2 className="text-lg font-semibold text-slate-900">Select Report Type</h2>
      <div className="space-y-3">
        {reportOptions.map((opt) => (
          <label
            key={opt.value}
            className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-colors ${
              reportType === opt.value
                ? "border-blue-500 bg-blue-50"
                : "border-slate-200 hover:border-slate-300"
            }`}
          >
            <input
              type="radio"
              name="reportType"
              value={opt.value}
              checked={reportType === opt.value}
              onChange={() => onReportTypeChange(opt.value)}
              className="mt-0.5 text-blue-600"
            />
            <div>
              <p className="text-sm font-medium text-slate-900">{opt.label}</p>
              <p className="text-xs text-slate-500">{opt.description}</p>
            </div>
          </label>
        ))}
      </div>

      {reportType === "custom" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <Input
            label="Start Date"
            type="date"
            value={startDate}
            onChange={(e) => onStartDateChange(e.target.value)}
          />
          <Input
            label="End Date"
            type="date"
            value={endDate}
            onChange={(e) => onEndDateChange(e.target.value)}
          />
        </div>
      )}

      <Button onClick={onSubmit} variant="primary">
        Generate Report
      </Button>
    </div>
  );
}

function ConfirmStep({
  reportType, startDate, endDate, isLoading, onConfirm, onBack,
}: {
  reportType: ReportType;
  startDate: string;
  endDate: string;
  isLoading: boolean;
  onConfirm: () => void;
  onBack: () => void;
}) {
  const description =
    reportType === "custom"
      ? `Custom range: ${startDate} to ${endDate}`
      : reportType === "monthly"
      ? "Current calendar month"
      : "Current calendar year (Jan 1 – Dec 31)";

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 space-y-4">
      <h2 className="text-lg font-semibold text-amber-900">Confirm Report Generation</h2>
      <p className="text-sm text-amber-800">
        The report will be submitted for:{" "}
        <span className="font-medium">{description}</span>
      </p>
      <div className="flex items-center gap-3">
        <Button onClick={onConfirm} disabled={isLoading}>
          {isLoading ? "Generating..." : "Confirm and Generate"}
        </Button>
        <Button variant="secondary" onClick={onBack} disabled={isLoading}>
          Cancel
        </Button>
      </div>
    </div>
  );
}

function ReportResults({
  result,
  onDownloadCsv,
}: {
  result: ReportResult;
  onDownloadCsv: () => void;
}) {
  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-900">Report Results</h2>
          <Button variant="secondary" size="sm" onClick={onDownloadCsv}>
            Download CSV
          </Button>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Stat label="Report Type" value={result.report_type.toUpperCase()} />
          <Stat label="Period" value={`${result.start_date} to ${result.end_date}`} />
          <Stat label="Total Transactions" value={String(result.total_transactions)} />
          <Stat
            label="Total Amount"
            value={formatAmount(result.total_amount)}
            colorClass={amountColorClass(result.total_amount)}
          />
        </div>
      </div>

      {/* Transaction table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                {["Transaction ID", "Date", "Card", "Description", "Merchant", "Amount"].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {result.transactions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-slate-400 text-sm">
                    No transactions in this period
                  </td>
                </tr>
              ) : (
                result.transactions.map((t) => (
                  <tr key={t.transaction_id} className="hover:bg-slate-50">
                    <td className="px-4 py-2 font-mono text-xs text-slate-700">{t.transaction_id}</td>
                    <td className="px-4 py-2 text-sm text-slate-600">{t.original_date}</td>
                    <td className="px-4 py-2 font-mono text-xs text-slate-500">{t.card_number}</td>
                    <td className="px-4 py-2 text-sm text-slate-700">{t.description}</td>
                    <td className="px-4 py-2 text-sm text-slate-600">{t.merchant_name}</td>
                    <td className={`px-4 py-2 text-sm font-semibold ${amountColorClass(t.amount)}`}>
                      {formatAmount(t.amount)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, colorClass = "text-slate-900" }: { label: string; value: string; colorClass?: string }) {
  return (
    <div>
      <dt className="text-xs text-slate-500 uppercase tracking-wide">{label}</dt>
      <dd className={`text-lg font-semibold ${colorClass}`}>{value}</dd>
    </div>
  );
}
