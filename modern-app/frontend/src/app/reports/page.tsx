/**
 * /reports — Transaction Reports page (CORPT00C modernization).
 */

import { ReportForm } from "@/components/Reports/ReportForm";

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Transaction Reports</h1>
        <p className="text-sm text-slate-500 mt-1 font-mono">CR00 / CORPT00C</p>
        <p className="text-sm text-slate-600 mt-2">
          Generate transaction reports for the current month, year, or a custom date range.
          Results can be viewed on-screen or downloaded as CSV.
        </p>
      </div>
      <ReportForm />
    </div>
  );
}
