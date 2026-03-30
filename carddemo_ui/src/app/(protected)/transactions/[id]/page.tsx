"use client";

import { useParams } from "next/navigation";
import TransactionDetail from "@/components/transactions/TransactionDetail";

export default function TransactionDetailPage() {
  const params = useParams();
  const tranId = params.id as string;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Transaction Details</h2>
      <TransactionDetail tranId={tranId} />
    </div>
  );
}
