"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AccountDetail from "@/components/accounts/AccountDetail";
import FormField from "@/components/ui/FormField";

export default function AccountViewPage() {
  const params = useParams();
  const router = useRouter();
  const paramId = params.id as string;
  const [inputId, setInputId] = useState(paramId === "0" ? "" : paramId);
  const [acctId, setAcctId] = useState(paramId === "0" ? "" : paramId);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputId) {
      setAcctId(inputId);
      router.replace(`/accounts/${inputId}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <h2 className="text-xl font-bold text-gray-900">Account View</h2>
        {acctId && (
          <button
            onClick={() => router.push(`/accounts/${acctId}/edit`)}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700"
          >
            Edit Account
          </button>
        )}
      </div>

      {/* Account ID Search */}
      <form onSubmit={handleSearch} className="flex items-end gap-3">
        <div className="w-48">
          <FormField
            label="Account ID"
            name="acct_id_search"
            type="number"
            value={inputId}
            onChange={(e) => setInputId(e.target.value)}
            placeholder="Enter account ID"
            required
          />
        </div>
        <button
          type="submit"
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700"
        >
          View
        </button>
      </form>

      {acctId && <AccountDetail acctId={acctId} />}
    </div>
  );
}
