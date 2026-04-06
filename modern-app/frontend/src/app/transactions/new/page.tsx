/**
 * /transactions/new — Add Transaction page (COTRN02C modernization).
 */

import { TransactionForm } from "@/components/Transactions/TransactionForm";

export default function AddTransactionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Add Transaction</h1>
        <p className="text-sm text-slate-500 mt-1 font-mono">CT02 / COTRN02C</p>
      </div>
      <TransactionForm />
    </div>
  );
}
