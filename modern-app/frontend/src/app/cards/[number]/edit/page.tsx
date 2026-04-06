"use client";

/**
 * /cards/[number]/edit — Card edit page.
 *
 * Modernizes COCRDUPC (Update Credit Card):
 *   - Account number PROTECTED (read-only display — ACCTSID PROT in BMS)
 *   - Editable: embossed name, active status (Y/N), expiry month/year
 *   - Validation: month 1-12, year 1950-2099, name non-blank, status Y/N
 *   - F5=Save -> PUT /api/cards/{number}
 *   - F12=Cancel -> back to card detail
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { CardForm } from "@/components/Cards/CardForm";
import type { CardDetail, CardUpdateRequest } from "@/types";

export default function CardEditPage() {
  const { number } = useParams<{ number: string }>();
  const { token } = useAuth();
  const [card, setCard] = useState<CardDetail | null>(null);
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

  const handleSave = async (payload: CardUpdateRequest): Promise<void> => {
    if (!token || !number) throw new Error("Not authenticated");
    await apiClient.updateCard(token, number, payload);
  };

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
      <CardForm card={card} onSave={handleSave} />
    </div>
  );
}
