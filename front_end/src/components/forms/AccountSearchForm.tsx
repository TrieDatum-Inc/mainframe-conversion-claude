/**
 * Account search/lookup form.
 * Mirrors the ACCTSID input field on both CACTVWA (view) and CACTUPA (update) screens.
 * BMS attributes: FSET, IC, NORM, UNPROT, PICIN='99999999999', VALIDN=MUSTFILL
 */

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Button } from "@/components/ui/Button";

interface AccountSearchFormProps {
  /** Destination route: 'view' or 'update' */
  mode: "view" | "update";
  /** Pre-filled account ID */
  defaultAcctId?: string;
}

export function AccountSearchForm({ mode, defaultAcctId = "" }: AccountSearchFormProps) {
  const router = useRouter();
  const [acctId, setAcctId] = useState(defaultAcctId);
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    // 2210-EDIT-ACCOUNT validation
    const trimmed = acctId.trim();
    if (!trimmed) {
      setError("Account number not provided");
      return;
    }
    if (!/^\d{1,11}$/.test(trimmed)) {
      setError("Account Filter must be a non-zero 11 digit number");
      return;
    }
    if (/^0+$/.test(trimmed)) {
      setError("Account number must be a non zero 11 digit number");
      return;
    }

    setError(null);
    const padded = trimmed.padStart(11, "0");
    const dest = mode === "view" ? `/accounts/${padded}` : `/accounts/${padded}/update`;
    router.push(dest);
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-3" aria-label="Account lookup">
      <div>
        <Label htmlFor="acct-id" required>
          Account Number
        </Label>
        <Input
          id="acct-id"
          type="text"
          inputMode="numeric"
          pattern="\d*"
          maxLength={11}
          value={acctId}
          onChange={(e) => {
            // PICIN='99999999999' — only digits allowed
            const val = e.target.value.replace(/\D/g, "");
            setAcctId(val);
            setError(null);
          }}
          placeholder="00000000001"
          autoFocus
          className="w-36 font-mono"
          aria-describedby={error ? "acct-id-error" : undefined}
          error={error ?? undefined}
        />
      </div>
      <Button type="submit" variant="primary">
        {mode === "view" ? "View" : "Update"}
      </Button>
      <Button
        type="button"
        variant="ghost"
        onClick={() => router.push("/")}
        aria-label="F3=Exit"
      >
        F3=Exit
      </Button>
    </form>
  );
}
