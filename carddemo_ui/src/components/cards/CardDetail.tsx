"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { CardDetail as CardDetailType } from "@/lib/types";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AlertMessage from "@/components/ui/AlertMessage";
import StatusBadge from "@/components/ui/StatusBadge";

interface CardDetailProps {
  cardNum: string;
}

export default function CardDetail({ cardNum }: CardDetailProps) {
  const [card, setCard] = useState<CardDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!cardNum) return;
    setLoading(true);
    setError("");
    api
      .get<CardDetailType>(`/api/cards/${cardNum}`)
      .then(setCard)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [cardNum]);

  if (loading) return <LoadingSpinner />;
  if (error) return <AlertMessage type="error" message={error} />;
  if (!card) return <AlertMessage type="info" message="Card not found." />;

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
          <h3 className="text-sm font-semibold text-gray-700">Card Details</h3>
        </div>
        <dl className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt className="text-xs font-medium text-gray-500">Card Number</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-900">{card.card_num}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Account ID</dt>
            <dd className="mt-1 text-sm text-gray-900">
              <Link href={`/accounts/${card.card_acct_id}`} className="text-brand-600 hover:underline">
                {card.card_acct_id}
              </Link>
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Status</dt>
            <dd className="mt-1">
              <StatusBadge status={card.card_active_status === "Y" ? "Active" : "Inactive"} />
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">CVV</dt>
            <dd className="mt-1 text-sm text-gray-900">{card.card_cvv_cd}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Embossed Name</dt>
            <dd className="mt-1 text-sm text-gray-900">{card.card_embossed_name}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Expiration Date</dt>
            <dd className="mt-1 text-sm text-gray-900">{card.card_expiration_date}</dd>
          </div>
        </dl>
      </section>

      <div className="flex gap-3">
        <Link
          href={`/cards/${cardNum}/edit`}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700"
        >
          Edit Card
        </Link>
        <Link
          href="/cards"
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
        >
          Back to List
        </Link>
      </div>
    </div>
  );
}
