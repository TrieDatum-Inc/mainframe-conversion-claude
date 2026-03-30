"use client";

import TransactionForm from "@/components/transactions/TransactionForm";

export default function NewTransactionPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Add Transaction</h2>
      <TransactionForm />
    </div>
  );
}
