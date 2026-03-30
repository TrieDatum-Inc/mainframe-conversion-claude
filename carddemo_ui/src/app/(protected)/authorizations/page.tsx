"use client";

import AuthSummaryTable from "@/components/authorizations/AuthSummaryTable";
import AuthDecisionForm from "@/components/authorizations/AuthDecisionForm";

export default function AuthorizationsPage() {
  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-xl font-bold text-gray-900">Pending Authorizations</h2>
        <div className="mt-4">
          <AuthSummaryTable />
        </div>
      </section>

      <section>
        <h2 className="text-xl font-bold text-gray-900">Authorization Decision</h2>
        <p className="mt-1 text-sm text-gray-500">
          Submit a card authorization request for real-time approval or decline.
        </p>
        <div className="mt-4">
          <AuthDecisionForm />
        </div>
      </section>
    </div>
  );
}
