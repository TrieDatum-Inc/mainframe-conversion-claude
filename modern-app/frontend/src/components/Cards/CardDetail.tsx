"use client";

/**
 * CardDetail — full credit card detail view.
 *
 * Modernizes COCRDSLC screen:
 *   - Displays all CARD-RECORD fields (CVACT02Y)
 *   - Account number shown (read-only, like ACCTSID output field)
 *   - Edit button navigates to update screen (COCRDUPC transition)
 *   - CVV displayed (internal admin view; would be masked in prod)
 */

import { useRouter } from "next/navigation";
import type { CardDetail as CardDetailType } from "@/types";

interface CardDetailProps {
  card: CardDetailType;
}

function formatDate(value: string | null): string {
  if (!value) return "--";
  const d = new Date(value);
  return `${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
}

function FieldRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="grid grid-cols-2 gap-4 py-3 border-b border-gray-50 last:border-b-0">
      <dt className="text-sm font-medium text-gray-500">{label}</dt>
      <dd className="text-sm text-gray-900 font-mono">{value ?? "--"}</dd>
    </div>
  );
}

export function CardDetail({ card }: CardDetailProps) {
  const router = useRouter();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Card Detail</h1>
          <p className="mt-1 text-sm font-mono text-gray-500">{card.card_number}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => router.push("/cards")}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Back to List
          </button>
          <button
            onClick={() => router.push(`/cards/${card.card_number}/edit`)}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Edit Card
          </button>
        </div>
      </div>

      {/* Card info */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-base font-semibold text-gray-900">Credit Card Information</h2>
        </div>
        <div className="px-6 py-4">
          <dl>
            <FieldRow label="Card Number" value={card.card_number} />
            <FieldRow
              label="Account Number"
              value={
                <button
                  onClick={() => router.push(`/accounts/${card.account_id}`)}
                  className="text-brand-600 hover:underline font-mono"
                >
                  {card.account_id}
                </button>
              }
            />
            <FieldRow label="Name on Card" value={card.embossed_name} />
            <FieldRow
              label="Status"
              value={
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                    card.active_status === "Y"
                      ? "bg-green-100 text-green-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  {card.active_status === "Y" ? "Active" : "Inactive"}
                </span>
              }
            />
            <FieldRow
              label="Expiry"
              value={formatDate(card.expiration_date)}
            />
            <FieldRow label="CVV" value={"***"} />
          </dl>
        </div>
      </div>
    </div>
  );
}
