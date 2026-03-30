"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { AuthDetailResponse } from "@/lib/types";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AlertMessage from "@/components/ui/AlertMessage";
import StatusBadge from "@/components/ui/StatusBadge";

interface AuthDetailViewProps {
  acctId: string;
}

export default function AuthDetailView({ acctId }: AuthDetailViewProps) {
  const [data, setData] = useState<AuthDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!acctId) return;
    setLoading(true);
    setError("");
    api
      .get<AuthDetailResponse>(`/api/authorizations/${acctId}/detail`)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [acctId]);

  if (loading) return <LoadingSpinner />;
  if (error) return <AlertMessage type="error" message={error} />;
  if (!data) return <AlertMessage type="info" message="No authorization data found." />;

  const currency = (val: number) =>
    new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(val);

  const { summary, details } = data;

  return (
    <div className="space-y-6">
      {/* Summary Section */}
      <section className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
          <h3 className="text-sm font-semibold text-gray-700">Authorization Summary — Account {acctId}</h3>
        </div>
        <dl className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt className="text-xs font-medium text-gray-500">Auth Status</dt>
            <dd className="mt-1"><StatusBadge status={summary.pa_auth_status} /></dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Credit Limit</dt>
            <dd className="mt-1 text-sm text-gray-900">{currency(summary.pa_credit_limit)}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Credit Balance</dt>
            <dd className="mt-1 text-sm text-gray-900">{currency(summary.pa_credit_balance)}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Cash Limit</dt>
            <dd className="mt-1 text-sm text-gray-900">{currency(summary.pa_cash_limit)}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Cash Balance</dt>
            <dd className="mt-1 text-sm text-gray-900">{currency(summary.pa_cash_balance)}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Approved Count</dt>
            <dd className="mt-1 text-sm text-gray-900">{summary.pa_approved_auth_cnt}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Declined Count</dt>
            <dd className="mt-1 text-sm text-gray-900">{summary.pa_declined_auth_cnt}</dd>
          </div>
        </dl>
      </section>

      {/* Detail Records */}
      <section className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
          <h3 className="text-sm font-semibold text-gray-700">Authorization Detail Records</h3>
        </div>
        {details.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-500">No detail records found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {["Date", "Time", "Card", "Type", "Amount", "Approved", "Response", "Merchant", "Status"].map(
                    (h) => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600">
                        {h}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {details.map((d) => (
                  <tr key={d.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-800">{d.pa_auth_date}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-800">{d.pa_auth_time}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-800">{d.pa_card_num}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-800">{d.pa_auth_type}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-800">{currency(d.pa_transaction_amt)}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-800">{currency(d.pa_approved_amt)}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-800">
                      <StatusBadge status={d.pa_auth_resp_code} />
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-800">{d.pa_merchant_name}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-800">
                      <StatusBadge status={d.auth_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <Link
        href="/authorizations"
        className="inline-block rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
      >
        Back to Summary
      </Link>
    </div>
  );
}
