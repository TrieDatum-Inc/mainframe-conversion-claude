"use client";

import { useParams } from "next/navigation";
import AccountForm from "@/components/accounts/AccountForm";

export default function AccountEditPage() {
  const params = useParams();
  const acctId = params.id as string;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Edit Account: {acctId}</h2>
      <AccountForm acctId={acctId} />
    </div>
  );
}
