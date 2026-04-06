"use client";

/**
 * CardTable — paginated card list with account and card number filters.
 *
 * Modernizes COCRDLIC (7-per-page browse):
 *   - Filter by account number (ACCTSID input)
 *   - Filter by card number (CARDSID input)
 *   - 7 rows per page (matches original F7/F8 paging)
 *   - Click row to view detail (replaces 'S' selector)
 *   - Click Edit to update card (replaces 'U' selector)
 *
 * Columns: Card Number | Account | Name on Card | Status | Expiry
 */

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { CardListItem } from "@/types";

interface CardTableProps {
  items: CardListItem[];
  total: number;
  page: number;
  totalPages: number;
  accountFilter: string;
  cardFilter: string;
  isLoading: boolean;
  onFilter: (accountId: string, cardNumber: string) => void;
  onPageChange: (page: number) => void;
}

function formatDate(value: string | null): string {
  if (!value) return "--";
  return new Date(value).toLocaleDateString("en-US", {
    month: "2-digit",
    year: "numeric",
  });
}

function maskCardNumber(cardNumber: string): string {
  if (cardNumber.length < 4) return cardNumber;
  return `****-****-****-${cardNumber.slice(-4)}`;
}

export function CardTable({
  items,
  total,
  page,
  totalPages,
  accountFilter,
  cardFilter,
  isLoading,
  onFilter,
  onPageChange,
}: CardTableProps) {
  const router = useRouter();
  const [acctInput, setAcctInput] = useState(accountFilter);
  const [cardInput, setCardInput] = useState(cardFilter);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilter(acctInput.trim(), cardInput.trim());
  };

  const handleClear = () => {
    setAcctInput("");
    setCardInput("");
    onFilter("", "");
  };

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <form onSubmit={handleFilterSubmit} className="flex flex-wrap gap-2">
        <input
          type="text"
          value={acctInput}
          onChange={(e) => setAcctInput(e.target.value)}
          placeholder="Account number..."
          className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          maxLength={11}
        />
        <input
          type="text"
          value={cardInput}
          onChange={(e) => setCardInput(e.target.value)}
          placeholder="Card number..."
          className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          maxLength={16}
        />
        <button
          type="submit"
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Filter
        </button>
        {(accountFilter || cardFilter) && (
          <button
            type="button"
            onClick={handleClear}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Clear
          </button>
        )}
      </form>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Card Number
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Account
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Name on Card
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Expiry
              </th>
              <th className="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-sm text-gray-500">
                  Loading...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-sm text-gray-500">
                  No cards found
                </td>
              </tr>
            ) : (
              items.map((card) => (
                <tr
                  key={card.card_number}
                  className="hover:bg-gray-50 transition-colors"
                >
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-mono text-gray-900">
                    {maskCardNumber(card.card_number)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-mono text-brand-700">
                    {card.account_id}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {card.embossed_name}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        card.active_status === "Y"
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {card.active_status === "Y" ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {formatDate(card.expiration_date)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                    <button
                      onClick={() => router.push(`/cards/${card.card_number}`)}
                      className="mr-3 text-brand-600 hover:underline"
                    >
                      View
                    </button>
                    <button
                      onClick={() => router.push(`/cards/${card.card_number}/edit`)}
                      className="text-gray-600 hover:underline"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-gray-700">
        <span>
          {total > 0
            ? `Showing page ${page} of ${totalPages} (${total} total)`
            : "No results"}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1 || isLoading}
            className="rounded border border-gray-300 px-3 py-1 disabled:opacity-40 hover:bg-gray-50"
          >
            Previous (F7)
          </button>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages || isLoading}
            className="rounded border border-gray-300 px-3 py-1 disabled:opacity-40 hover:bg-gray-50"
          >
            Next (F8)
          </button>
        </div>
      </div>
    </div>
  );
}
