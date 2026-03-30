"use client";

import BillPaymentForm from "@/components/billing/BillPaymentForm";

export default function BillPaymentPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Bill Payment</h2>
      <p className="text-sm text-gray-500">
        Enter an account ID to preview and pay the outstanding balance.
      </p>
      <BillPaymentForm />
    </div>
  );
}
