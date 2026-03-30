"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { TransactionDetail as TransactionDetailType } from "@/lib/types";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AlertMessage from "@/components/ui/AlertMessage";

interface TransactionDetailProps {
  tranId: string;
}

export default function TransactionDetail({ tranId }: TransactionDetailProps) {
  const [txn, setTxn] = useState<TransactionDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!tranId) return;
    setLoading(true);
    setError("");
    api
      .get<TransactionDetailType>(`/api/transactions/${tranId}`)
      .then(setTxn)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [tranId]);

  if (loading) return <LoadingSpinner />;
  if (error) return <AlertMessage type="error" message={error} />;
  if (!txn) return <AlertMessage type="info" message="Transaction not found." />;

  const currency = (val: number) =>
    new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(val);

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
          <h3 className="text-sm font-semibold text-gray-700">Transaction Details</h3>
        </div>
        <dl className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt className="text-xs font-medium text-gray-500">Transaction ID</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-900">{txn.tran_id}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Type Code</dt>
            <dd className="mt-1 text-sm text-gray-900">{txn.tran_type_cd}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Category Code</dt>
            <dd className="mt-1 text-sm text-gray-900">{txn.tran_cat_cd}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Source</dt>
            <dd className="mt-1 text-sm text-gray-900">{txn.tran_source}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-xs font-medium text-gray-500">Description</dt>
            <dd className="mt-1 text-sm text-gray-900">{txn.tran_desc}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Amount</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-900">{currency(txn.tran_amt)}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Card Number</dt>
            <dd className="mt-1 text-sm text-gray-900">
              <Link href={`/cards/${txn.tran_card_num}`} className="text-brand-600 hover:underline">
                {txn.tran_card_num}
              </Link>
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Originated</dt>
            <dd className="mt-1 text-sm text-gray-900">{txn.tran_orig_ts}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Processed</dt>
            <dd className="mt-1 text-sm text-gray-900">{txn.tran_proc_ts}</dd>
          </div>
        </dl>
      </section>

      {/* Merchant Information */}
      <section className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
          <h3 className="text-sm font-semibold text-gray-700">Merchant Information</h3>
        </div>
        <dl className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt className="text-xs font-medium text-gray-500">Merchant ID</dt>
            <dd className="mt-1 text-sm text-gray-900">{txn.tran_merchant_id}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Merchant Name</dt>
            <dd className="mt-1 text-sm text-gray-900">{txn.tran_merchant_name}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">City</dt>
            <dd className="mt-1 text-sm text-gray-900">{txn.tran_merchant_city}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">ZIP</dt>
            <dd className="mt-1 text-sm text-gray-900">{txn.tran_merchant_zip}</dd>
          </div>
        </dl>
      </section>

      <Link
        href="/transactions"
        className="inline-block rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
      >
        Back to List
      </Link>
    </div>
  );
}
