"use client";

import { useParams } from "next/navigation";
import AuthDetailView from "@/components/authorizations/AuthDetailView";

export default function AuthDetailPage() {
  const params = useParams();
  const acctId = params.acctId as string;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Authorization Details</h2>
      <AuthDetailView acctId={acctId} />
    </div>
  );
}
