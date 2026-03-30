"use client";

import TranTypeForm from "@/components/transaction-types/TranTypeForm";

export default function NewTransactionTypePage() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Add Transaction Type</h2>
      <TranTypeForm />
    </div>
  );
}
