"use client";

/**
 * ReportsClient — maps CORPT00 BMS screen (CORPT0A map).
 *
 * BMS screen layout reference:
 *   Row 4:  "Transaction Reports" heading (BRT, NEUTRAL)
 *   Row 7:  [ ] Monthly (Current Month)     — MONTHLY field (GREEN, IC)
 *   Row 9:  [ ] Yearly (Current Year)       — YEARLY field (GREEN)
 *   Row 11: [ ] Custom (Date Range)         — CUSTOM field (GREEN)
 *   Row 13: Start Date: MM / DD / YYYY      — SDTMM, SDTDD, SDTYYYY (GREEN, NUM)
 *   Row 14: End Date:   MM / DD / YYYY      — EDTMM, EDTDD, EDTYYYY (GREEN, NUM)
 *   Row 19: "The Report will be submitted... Please confirm:" Y/N  — CONFIRM (GREEN)
 *   Row 23: [ERRMSG] — ASKIP,BRT,FSET,RED (errors) or GREEN (success)
 *   Row 24: ENTER=Continue  F3=Back
 *
 * Two-step flow:
 *   Step 1: User selects report type + dates (if custom)
 *   Step 2: CONFIRM=Y modal/inline confirmation → POST /reports → success message (GREEN)
 *   CONFIRM=N: Re-initialize all fields (INITIALIZE-ALL-FIELDS equivalent)
 *
 * Business rules implemented:
 *   BR-001: Must select exactly one report type
 *   BR-006/007: Custom dates validated by date input (browser + API)
 *   BR-008: start_date <= end_date (client-side + API validation)
 *   BR-009: CONFIRM must be Y to submit
 */
import { useState } from "react";
import { useRouter } from "next/navigation";

import { submitReport } from "@/lib/api";
import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { PFKeyBar } from "@/components/ui/PFKeyBar";
import { getErrorMessage } from "@/lib/utils";
import type { MessageType, ReportJobResponse, ReportType } from "@/types";

// ============================================================
// Confirmation dialog component — maps CORPT00C CONFIRM field
// ============================================================
interface ConfirmDialogProps {
  reportType: ReportType;
  startDate: string;
  endDate: string;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading: boolean;
}

function ConfirmDialog({
  reportType,
  startDate,
  endDate,
  onConfirm,
  onCancel,
  isLoading,
}: ConfirmDialogProps) {
  const displayType = reportType.charAt(0).toUpperCase() + reportType.slice(1);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 border border-yellow-600 rounded-lg p-6 max-w-md w-full mx-4 font-mono">
        <h2 className="text-yellow-400 text-lg font-bold mb-4">
          Confirm Report Submission
        </h2>
        <p className="text-cyan-400 mb-2">
          The Report will be submitted for printing. Please confirm:
        </p>
        <div className="bg-gray-800 p-3 rounded mb-4 text-sm">
          <p className="text-green-400">
            Type: <span className="text-white">{displayType}</span>
          </p>
          <p className="text-green-400">
            Period:{" "}
            <span className="text-white">
              {startDate} to {endDate}
            </span>
          </p>
        </div>
        <p className="text-gray-400 text-xs mb-4">
          (Y/N) — Enter Y to submit, N to cancel
        </p>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 bg-green-700 hover:bg-green-600 disabled:bg-gray-600 text-white font-mono py-2 px-4 rounded transition-colors"
            aria-label="Confirm: Y — Submit report"
          >
            {isLoading ? "Submitting..." : "Y — Confirm"}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1 bg-red-800 hover:bg-red-700 disabled:bg-gray-600 text-white font-mono py-2 px-4 rounded transition-colors"
            aria-label="Cancel: N — Do not submit"
          >
            N — Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// Main ReportsClient component
// ============================================================

export function ReportsClient() {
  const router = useRouter();

  // Report type selection — maps MONTHLYI / YEARLYI / CUSTOMI radio fields
  const [reportType, setReportType] = useState<ReportType | null>(null);

  // Custom date range — maps SDTMM/SDTDD/SDTYYYY and EDTMM/EDTDD/EDTYYYY
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");

  // Status and messaging — maps WS-MESSAGE / ERRMSG field
  const [message, setMessage] = useState<string | null>(null);
  const [messageType, setMessageType] = useState<MessageType>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [lastJob, setLastJob] = useState<ReportJobResponse | null>(null);

  // Compute preview dates for display in confirm dialog
  const previewDates = (() => {
    if (reportType === "monthly") {
      const now = new Date();
      const start = new Date(now.getFullYear(), now.getMonth(), 1);
      const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
      return {
        start: start.toISOString().split("T")[0],
        end: end.toISOString().split("T")[0],
      };
    }
    if (reportType === "yearly") {
      const yr = new Date().getFullYear();
      return { start: `${yr}-01-01`, end: `${yr}-12-31` };
    }
    return { start: startDate, end: endDate };
  })();

  // ============================================================
  // PROCESS-ENTER-KEY equivalent
  // ============================================================
  function handleEnter(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);
    setLastJob(null);

    // BR-001: Must select a report type
    if (!reportType) {
      setMessage("Select a report type to print report...");
      setMessageType("error");
      return;
    }

    // Custom path: validate dates present
    if (reportType === "custom") {
      if (!startDate) {
        setMessage("Start date is required for custom date range");
        setMessageType("error");
        return;
      }
      if (!endDate) {
        setMessage("End date is required for custom date range");
        setMessageType("error");
        return;
      }
      // BR-008: start <= end
      if (startDate > endDate) {
        setMessage("Start date must be on or before end date");
        setMessageType("error");
        return;
      }
    }

    // Show confirmation dialog (CONFIRM field prompt)
    setShowConfirm(true);
  }

  // ============================================================
  // SUBMIT-JOB-TO-INTRDR equivalent — CONFIRM=Y path
  // ============================================================
  async function handleConfirmSubmit() {
    if (!reportType) return;
    setIsLoading(true);
    try {
      const payload =
        reportType === "custom"
          ? { report_type: reportType, start_date: startDate, end_date: endDate }
          : { report_type: reportType };

      const job = await submitReport(payload);
      setLastJob(job);
      // CORPT00C: after successful submission, re-initialize all fields
      // and show success in GREEN (messageType='success')
      setReportType(null);
      setStartDate("");
      setEndDate("");
      setMessage(job.message);
      setMessageType("success");
      setShowConfirm(false);
    } catch (err) {
      const e = err as Record<string, unknown>;
      if ((e.status as number) === 401) {
        router.push("/login");
        return;
      }
      setMessage(getErrorMessage(err));
      setMessageType("error");
      setShowConfirm(false);
    } finally {
      setIsLoading(false);
    }
  }

  // CONFIRM=N path — INITIALIZE-ALL-FIELDS equivalent
  function handleConfirmCancel() {
    setShowConfirm(false);
    setReportType(null);
    setStartDate("");
    setEndDate("");
    setMessage(null);
  }

  // PF3=Back — XCTL to main menu (COMEN01C)
  function handleBack() {
    router.push("/main-menu");
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col font-mono">
      {/* Confirmation dialog overlay */}
      {showConfirm && reportType && (
        <ConfirmDialog
          reportType={reportType}
          startDate={previewDates.start}
          endDate={previewDates.end}
          onConfirm={handleConfirmSubmit}
          onCancel={handleConfirmCancel}
          isLoading={isLoading}
        />
      )}

      {/* Header — POPULATE-HEADER-INFO equivalent */}
      <ScreenHeader
        transactionId="CR00"
        programName="CORPT00C"
        title01="AWS Mainframe Modernization"
        title02="CardDemo"
      />

      {/* Main screen content — 24x80 terminal layout */}
      <main className="flex-1 p-4 max-w-4xl mx-auto w-full">
        {/* Row 4: Screen heading — BRT, NEUTRAL */}
        <h1 className="text-center text-white font-bold text-lg mb-6 mt-2">
          Transaction Reports
        </h1>

        <form onSubmit={handleEnter} noValidate>
          {/* Report type selection — rows 7, 9, 11 */}
          <div className="mb-6">
            <div className="space-y-3">
              {/* Row 7: MONTHLY — FSET,IC,NORM,UNPROT,GREEN */}
              <label className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="radio"
                  name="reportType"
                  value="monthly"
                  checked={reportType === "monthly"}
                  onChange={() => {
                    setReportType("monthly");
                    setMessage(null);
                  }}
                  className="w-4 h-4 text-green-500 bg-gray-800 border-gray-600 focus:ring-green-500"
                  aria-label="Monthly report (current month)"
                />
                <span className="text-green-400 w-4">
                  {reportType === "monthly" ? "X" : " "}
                </span>
                {/* TURQUOISE,BRT label */}
                <span className="text-cyan-400 font-bold">
                  Monthly (Current Month)
                </span>
              </label>

              {/* Row 9: YEARLY */}
              <label className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="radio"
                  name="reportType"
                  value="yearly"
                  checked={reportType === "yearly"}
                  onChange={() => {
                    setReportType("yearly");
                    setMessage(null);
                  }}
                  className="w-4 h-4 text-green-500 bg-gray-800 border-gray-600 focus:ring-green-500"
                  aria-label="Yearly report (current year)"
                />
                <span className="text-green-400 w-4">
                  {reportType === "yearly" ? "X" : " "}
                </span>
                <span className="text-cyan-400 font-bold">
                  Yearly (Current Year)
                </span>
              </label>

              {/* Row 11: CUSTOM */}
              <label className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="radio"
                  name="reportType"
                  value="custom"
                  checked={reportType === "custom"}
                  onChange={() => {
                    setReportType("custom");
                    setMessage(null);
                  }}
                  className="w-4 h-4 text-green-500 bg-gray-800 border-gray-600 focus:ring-green-500"
                  aria-label="Custom date range report"
                />
                <span className="text-green-400 w-4">
                  {reportType === "custom" ? "X" : " "}
                </span>
                <span className="text-cyan-400 font-bold">
                  Custom (Date Range)
                </span>
              </label>
            </div>
          </div>

          {/* Custom date range — rows 13-14, shown only when CUSTOM selected */}
          {reportType === "custom" && (
            <div className="mb-6 pl-8 border-l-2 border-gray-700">
              {/* Row 13: Start Date — SDTMM/SDTDD/SDTYYYY (NUM,UNPROT,GREEN) */}
              <div className="flex items-center gap-3 mb-3">
                <span className="text-cyan-400 w-28">Start Date :</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => {
                    setStartDate(e.target.value);
                    setMessage(null);
                  }}
                  className="bg-gray-800 border border-green-600 text-green-400 font-mono px-2 py-1 rounded focus:outline-none focus:ring-1 focus:ring-green-500 underline"
                  aria-label="Start date (MM/DD/YYYY)"
                  required
                />
                <span className="text-blue-400 text-xs">(MM/DD/YYYY)</span>
              </div>

              {/* Row 14: End Date — EDTMM/EDTDD/EDTYYYY */}
              <div className="flex items-center gap-3">
                <span className="text-cyan-400 w-28">End Date :</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => {
                    setEndDate(e.target.value);
                    setMessage(null);
                  }}
                  className="bg-gray-800 border border-green-600 text-green-400 font-mono px-2 py-1 rounded focus:outline-none focus:ring-1 focus:ring-green-500 underline"
                  aria-label="End date (MM/DD/YYYY)"
                  required
                />
                <span className="text-blue-400 text-xs">(MM/DD/YYYY)</span>
              </div>
            </div>
          )}

          {/* Row 19: Confirm prompt indicator */}
          <div className="mb-4 text-cyan-400 text-sm">
            The Report will be submitted for printing. Please confirm: (Y/N) on
            next screen
          </div>

          {/* Submit button — ENTER key equivalent */}
          <div className="mb-4">
            <button
              type="submit"
              disabled={isLoading}
              className="bg-blue-800 hover:bg-blue-700 disabled:bg-gray-700 text-white font-mono py-2 px-6 rounded transition-colors"
              aria-label="Submit report request (ENTER)"
            >
              {isLoading ? "Submitting..." : "ENTER — Continue"}
            </button>
          </div>

          {/* Recent submission result */}
          {lastJob && (
            <div className="mb-4 bg-gray-800 p-3 rounded border border-green-600 text-sm">
              <p className="text-green-400 font-bold">Last Submission:</p>
              <p className="text-gray-300">Job ID: {lastJob.job_id}</p>
              <p className="text-gray-300">
                Period: {lastJob.start_date} to {lastJob.end_date}
              </p>
              <p className="text-gray-300">Status: {lastJob.status}</p>
            </div>
          )}
        </form>

        {/* Row 23: ERRMSG */}
        <ErrorMessage message={message} messageType={messageType} />
      </main>

      {/* Row 24: PF key legend — ENTER=Continue  F3=Back */}
      <PFKeyBar
        keys={[
          { key: "ENTER", label: "Continue" },
          { key: "F3", label: "Back", onClick: handleBack },
        ]}
      />
    </div>
  );
}
