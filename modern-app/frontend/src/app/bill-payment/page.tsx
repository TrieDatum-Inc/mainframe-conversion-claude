/**
 * /bill-payment — Bill Payment page (COBIL00C modernization).
 */

import { BillPaymentForm } from "@/components/BillPayment/BillPaymentForm";

export default function BillPaymentPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Bill Payment</h1>
        <p className="text-sm text-slate-500 mt-1 font-mono">CB00 / COBIL00C</p>
        <p className="text-sm text-slate-600 mt-2">
          Pay the full outstanding balance for your account. Payments are always for the
          complete balance — partial payments are not supported.
        </p>
      </div>
      <BillPaymentForm />
    </div>
  );
}
