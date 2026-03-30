"use client";

import ReportForm from "@/components/reports/ReportForm";

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Transaction Reports</h2>
      <p className="text-sm text-gray-500">
        Generate monthly, yearly, or custom-range transaction reports.
      </p>
      <ReportForm />
    </div>
  );
}
