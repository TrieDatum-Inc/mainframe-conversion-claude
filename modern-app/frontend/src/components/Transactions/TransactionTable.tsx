"use client";

/**
 * TransactionTable — modern data table replacing COTRN00C paginated list.
 *
 * Columns:  Transaction ID | Date | Description | Amount
 * Colors:   Green for credits (amount >= 0), Red for debits (amount < 0)
 * Clicking a row navigates to /transactions/[id] (mirrors 'S' select in COTRN00C).
 */

import { useRouter } from "next/navigation";
import { amountColorClass, formatAmount, truncate } from "@/lib/utils";
import type { TransactionListItem, TransactionPage } from "@/types";
import { Button } from "@/components/ui/Button";

interface TransactionTableProps {
  data: TransactionPage;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
}

export function TransactionTable({ data, onPageChange, isLoading }: TransactionTableProps) {
  const router = useRouter();

  function handleRowClick(transactionId: string) {
    router.push(`/transactions/${transactionId}`);
  }

  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="p-8 text-center text-slate-400 text-sm">Loading transactions...</div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                Transaction ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                Card
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                Description
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">
                Amount
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400 text-sm">
                  No transactions found
                </td>
              </tr>
            ) : (
              data.items.map((txn) => (
                <TransactionRow key={txn.transaction_id} txn={txn} onClick={handleRowClick} />
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <Pagination data={data} onPageChange={onPageChange} />
    </div>
  );
}

function TransactionRow({
  txn,
  onClick,
}: {
  txn: TransactionListItem;
  onClick: (id: string) => void;
}) {
  return (
    <tr
      className="hover:bg-blue-50 cursor-pointer transition-colors"
      onClick={() => onClick(txn.transaction_id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick(txn.transaction_id)}
      aria-label={`View transaction ${txn.transaction_id}`}
    >
      <td className="px-4 py-3 font-mono text-xs text-slate-700">{txn.transaction_id}</td>
      <td className="px-4 py-3 text-sm text-slate-600">{txn.original_date}</td>
      <td className="px-4 py-3 font-mono text-xs text-slate-500">
        {txn.card_number.replace(/(\d{4})(?=\d)/g, "$1 ")}
      </td>
      <td className="px-4 py-3 text-sm text-slate-700">
        {truncate(txn.description, 40)}
      </td>
      <td className={`px-4 py-3 text-sm font-semibold text-right ${amountColorClass(txn.amount)}`}>
        {formatAmount(txn.amount)}
      </td>
    </tr>
  );
}

function Pagination({
  data,
  onPageChange,
}: {
  data: TransactionPage;
  onPageChange: (page: number) => void;
}) {
  const start = (data.page - 1) * data.page_size + 1;
  const end = Math.min(data.page * data.page_size, data.total);

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200 bg-slate-50">
      <p className="text-sm text-slate-600">
        {data.total === 0
          ? "No results"
          : `Showing ${start}–${end} of ${data.total} transactions`}
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          disabled={!data.has_prev}
          onClick={() => onPageChange(data.page - 1)}
          aria-label="Previous page"
        >
          Previous
        </Button>
        <span className="text-sm text-slate-600 px-2">Page {data.page}</span>
        <Button
          variant="secondary"
          size="sm"
          disabled={!data.has_next}
          onClick={() => onPageChange(data.page + 1)}
          aria-label="Next page"
        >
          Next
        </Button>
      </div>
    </div>
  );
}
