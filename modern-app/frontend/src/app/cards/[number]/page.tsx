"use client";

/**
 * /cards/[number] — Card detail page.
 *
 * Modernizes COCRDSLC (View Credit Card Detail):
 *   - READ CARDDAT by CARD-NUM
 *   - Displays all CARD-RECORD fields
 *   - Edit button navigates to /cards/[number]/edit (COCRDUPC)
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { CardDetail } from "@/components/Cards/CardDetail";
import type { CardDetail as CardDetailType } from "@/types";

export default function CardDetailPage() {
  const { number } = useParams<{ number: string }>();
  const { token } = useAuth();
  const [card, setCard] = useState<CardDetailType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !number) return;
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiClient.getCard(token, number);
        setCard(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load card");
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [token, number]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <div className="text-sm text-gray-500">Loading card...</div>
      </div>
    );
  }

  if (error || !card) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error || "Card not found"}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
      <CardDetail card={card} />
    </div>
  );
}
