"use client";

/**
 * TransactionDetail — displays all 13 output fields from COTRN01C.
 *
 * Sections:
 *   Transaction Info: ID, card, type, category, source
 *   Financial:        amount, original date, processing date
 *   Merchant:         ID, name, city, zip
 */

import { amountColorClass, formatAmount, formatDate } from "@/lib/utils";
import type { TransactionDetail as TxnDetail } from "@/types";
import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";

interface TransactionDetailProps {
  transaction: TxnDetail;
}

export function TransactionDetailView({ transaction: t }: TransactionDetailProps) {
  const router = useRouter();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Transaction Detail</h1>
          <p className="mt-1 font-mono text-sm text-slate-500">ID: {t.transaction_id}</p>
        </div>
        <Button variant="secondary" onClick={() => router.back()}>
          Back
        </Button>
      </div>

      {/* Transaction Info */}
      <DetailCard title="Transaction Information">
        <DetailRow label="Transaction ID" value={t.transaction_id} mono />
        <DetailRow
          label="Card Number"
          value={t.card_number.replace(/(\d{4})(?=\d)/g, "$1 ")}
          mono
        />
        <DetailRow label="Type Code" value={t.type_code} />
        <DetailRow label="Category Code" value={t.category_code} />
        <DetailRow label="Source" value={t.source} />
        <DetailRow label="Description" value={t.description} />
      </DetailCard>

      {/* Financial */}
      <DetailCard title="Financial Details">
        <div className="py-2 border-b border-slate-100 last:border-0">
          <dt className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
            Amount
          </dt>
          <dd className={`text-xl font-bold ${amountColorClass(t.amount)}`}>
            {formatAmount(t.amount)}
          </dd>
        </div>
        <DetailRow label="Original Date" value={formatDate(t.original_timestamp)} />
        <DetailRow label="Processing Date" value={formatDate(t.processing_timestamp)} />
      </DetailCard>

      {/* Merchant */}
      <DetailCard title="Merchant Information">
        <DetailRow label="Merchant ID" value={t.merchant_id} mono />
        <DetailRow label="Merchant Name" value={t.merchant_name} />
        <DetailRow label="City" value={t.merchant_city} />
        <DetailRow label="ZIP Code" value={t.merchant_zip} />
      </DetailCard>

      {/* Audit */}
      <DetailCard title="Audit">
        <DetailRow label="Created" value={new Date(t.created_at).toLocaleString()} />
        <DetailRow label="Last Updated" value={new Date(t.updated_at).toLocaleString()} />
      </DetailCard>
    </div>
  );
}

function DetailCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="bg-slate-50 px-6 py-3 border-b border-slate-200">
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">
          {title}
        </h2>
      </div>
      <dl className="divide-y divide-slate-100 px-6">{children}</dl>
    </div>
  );
}

function DetailRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="py-3 flex items-start gap-4">
      <dt className="w-36 flex-shrink-0 text-xs font-medium text-slate-500 uppercase tracking-wide pt-0.5">
        {label}
      </dt>
      <dd className={`text-sm text-slate-900 ${mono ? "font-mono" : ""}`}>
        {value || <span className="text-slate-400 italic">—</span>}
      </dd>
    </div>
  );
}
