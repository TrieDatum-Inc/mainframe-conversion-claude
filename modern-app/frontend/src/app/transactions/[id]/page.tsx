"use client";

/**
 * /transactions/[id] — Transaction detail page (COTRN01C modernization).
 *
 * Displays all 13 output fields from the COTRN01C BMS screen in a clean card layout.
 */

import { useEffect, useState } from "react";
import { getTransaction } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import { TransactionDetailView } from "@/components/Transactions/TransactionDetail";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import type { TransactionDetail } from "@/types";

interface PageProps {
  params: { id: string };
}

export default function TransactionDetailPage({ params }: PageProps) {
  const router = useRouter();
  const [transaction, setTransaction] = useState<TransactionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await getTransaction(params.id);
        setTransaction(data);
      } catch (e) {
        setError(getErrorMessage(e));
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [params.id]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-400 text-sm">
        Loading transaction...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Alert variant="error" title="Transaction Not Found" message={error} />
        <Button variant="secondary" onClick={() => router.back()}>
          Go Back
        </Button>
      </div>
    );
  }

  if (!transaction) return null;

  return <TransactionDetailView transaction={transaction} />;
}
