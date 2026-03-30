"use client";

import Link from "next/link";
import TransactionTable from "@/components/transactions/TransactionTable";

export default function TransactionsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Transactions</h2>
        <Link
          href="/transactions/new"
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700"
        >
          Add Transaction
        </Link>
      </div>
      <TransactionTable />
    </div>
  );
}
