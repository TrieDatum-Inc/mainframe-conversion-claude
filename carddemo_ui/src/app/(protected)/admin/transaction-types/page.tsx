"use client";

import Link from "next/link";
import TranTypeTable from "@/components/transaction-types/TranTypeTable";

export default function TransactionTypesPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Transaction Types</h2>
        <Link
          href="/admin/transaction-types/new"
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700"
        >
          Add Type
        </Link>
      </div>
      <TranTypeTable />
    </div>
  );
}
