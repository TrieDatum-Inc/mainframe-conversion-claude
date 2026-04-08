"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuthStore } from "@/stores/auth-store";
import { getCard, updateCard, extractErrorMessage, extractErrorCode } from "@/lib/api";
import { AppHeader } from "@/components/layout/AppHeader";
import { MessageBar } from "@/components/ui/MessageBar";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import type { CardDetailResponse } from "@/types";

// ---------------------------------------------------------------------------
// Zod schema — mirrors backend CardUpdateRequest
// card_embossed_name: letters and spaces only (INSPECT CONVERTING equivalent)
// expiration_month: 1-12
// expiration_year: 1950-2099
// active_status: Y or N
// ---------------------------------------------------------------------------

const cardUpdateSchema = z.object({
  card_embossed_name: z
    .string()
    .min(1, "Name is required")
    .max(50)
    .regex(/^[A-Za-z\s]+$/, "Name must contain only letters and spaces")
    .transform((v) => v.toUpperCase()),
  active_status: z.enum(["Y", "N"]),
  expiration_month: z.coerce
    .number()
    .int()
    .min(1, "Month must be 1-12")
    .max(12, "Month must be 1-12"),
  expiration_year: z.coerce
    .number()
    .int()
    .min(1950, "Year must be 1950-2099")
    .max(2099, "Year must be 1950-2099"),
  optimistic_lock_version: z.string().min(1),
});

type CardUpdateFormValues = z.infer<typeof cardUpdateSchema>;

/**
 * Card Update page — COCRDUPC.
 * Editable: embossed name, active_status, expiration_month, expiration_year.
 * PROT (read-only): card_number, account_id.
 * Optimistic locking: updated_at from GET response must match current DB value.
 */
function CardUpdateContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuthStore();

  const [cardNumberInput, setCardNumberInput] = useState(
    searchParams.get("card_number") || ""
  );
  const [card, setCard] = useState<CardDetailResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CardUpdateFormValues>({
    resolver: zodResolver(cardUpdateSchema),
  });

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  useEffect(() => {
    const cn = searchParams.get("card_number");
    if (cn) fetchCard(cn);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchCard(cardNumber: string) {
    setLoading(true);
    setErrorMsg(null);
    setCard(null);
    try {
      const data = await getCard(cardNumber.trim());
      setCard(data);
      reset({
        card_embossed_name: data.card_embossed_name,
        active_status: data.active_status,
        expiration_month: data.expiration_month ?? 1,
        expiration_year: data.expiration_year ?? 2025,
        optimistic_lock_version: data.updated_at,
      });
    } catch (err) {
      setErrorMsg(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!cardNumberInput.trim()) {
      setErrorMsg("CARD NUMBER IS REQUIRED");
      return;
    }
    fetchCard(cardNumberInput);
  }

  async function onSubmit(values: CardUpdateFormValues) {
    if (!card) return;
    setSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await updateCard(card.card_number, {
        card_embossed_name: values.card_embossed_name,
        active_status: values.active_status,
        expiration_month: values.expiration_month,
        expiration_year: values.expiration_year,
        optimistic_lock_version: values.optimistic_lock_version,
      });
      setSuccessMsg("CARD UPDATED SUCCESSFULLY");
      // Re-fetch to get fresh updated_at (new optimistic lock token)
      fetchCard(card.card_number);
    } catch (err) {
      const code = extractErrorCode(err);
      if (code === "OPTIMISTIC_LOCK_ERROR") {
        setErrorMsg(
          "RECORD WAS MODIFIED BY ANOTHER USER - PLEASE RE-FETCH AND TRY AGAIN"
        );
      } else {
        setErrorMsg(extractErrorMessage(err));
      }
    } finally {
      setSaving(false);
    }
  }

  if (!isAuthenticated) {
    return null; // Prevent flash before redirect fires
  }

  return (
    <div className="min-h-screen bg-mainframe-bg">
      <AppHeader
        title="CREDIT CARD UPDATE"
        subtitle="COCRDUPC - UPDATE CARD EMBOSSED NAME AND EXPIRY"
      />

      <main className="container mx-auto px-4 py-6 max-w-3xl">
        {/* Search */}
        <form onSubmit={handleSearch} className="border border-mainframe-border p-4 mb-4">
          <div className="flex items-center space-x-4">
            <label className="text-mainframe-dim text-xs w-24">CARD NUM:</label>
            <input
              type="text"
              value={cardNumberInput}
              onChange={(e) => setCardNumberInput(e.target.value)}
              maxLength={16}
              className="px-2 py-1 text-sm w-40 font-mono"
              placeholder="________________"
            />
            <button
              type="button"
              onClick={handleSearch}
              className="px-4 py-1 text-sm bg-mainframe-border text-mainframe-text hover:bg-mainframe-panel"
            >
              [ FETCH ]
            </button>
          </div>
        </form>

        {/* Messages */}
        {errorMsg && (
          <div className="mb-4">
            <MessageBar type="error" message={errorMsg} onDismiss={() => setErrorMsg(null)} />
          </div>
        )}
        {successMsg && (
          <div className="mb-4">
            <MessageBar type="success" message={successMsg} onDismiss={() => setSuccessMsg(null)} />
          </div>
        )}

        {loading && <LoadingSpinner message="FETCHING CARD..." />}

        {card && !loading && (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="border border-mainframe-border p-4">
              <h2 className="text-mainframe-info text-sm font-bold mb-4 border-b border-mainframe-border pb-2">
                CARD UPDATE
              </h2>

              <div className="space-y-4 text-xs">
                {/* Read-only fields (PROT) */}
                <ReadOnlyField label="CARD NUMBER" value={card.card_number} mono />
                <ReadOnlyField label="ACCOUNT ID" value={String(card.account_id)} />

                {/* Hidden optimistic lock field */}
                <input type="hidden" {...register("optimistic_lock_version")} />

                {/* Editable fields (UNPROT) */}
                <div>
                  <label htmlFor="card-embossed-name" className="block text-mainframe-dim mb-1">EMBOSSED NAME:</label>
                  <input
                    id="card-embossed-name"
                    {...register("card_embossed_name")}
                    type="text"
                    maxLength={50}
                    className="px-2 py-1 text-sm w-64 uppercase"
                    placeholder="CARDHOLDER NAME"
                  />
                  {errors.card_embossed_name && (
                    <p className="text-mainframe-error text-xs mt-1">
                      {errors.card_embossed_name.message}
                    </p>
                  )}
                  <p className="text-mainframe-dim text-xs mt-1">
                    LETTERS AND SPACES ONLY (ALPHA CHARS)
                  </p>
                </div>

                <div>
                  <label htmlFor="card-active-status" className="block text-mainframe-dim mb-1">STATUS:</label>
                  <select
                    id="card-active-status"
                    {...register("active_status")}
                    className="px-2 py-1 text-sm w-24"
                  >
                    <option value="Y">Y - ACTIVE</option>
                    <option value="N">N - INACTIVE</option>
                  </select>
                  {errors.active_status && (
                    <p className="text-mainframe-error text-xs mt-1">
                      {errors.active_status.message}
                    </p>
                  )}
                </div>

                <div className="flex space-x-6">
                  <div>
                    <label htmlFor="card-exp-month" className="block text-mainframe-dim mb-1">EXP MONTH (1-12):</label>
                    <input
                      id="card-exp-month"
                      {...register("expiration_month")}
                      type="number"
                      min={1}
                      max={12}
                      className="px-2 py-1 text-sm w-16"
                    />
                    {errors.expiration_month && (
                      <p className="text-mainframe-error text-xs mt-1">
                        {errors.expiration_month.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="card-exp-year" className="block text-mainframe-dim mb-1">EXP YEAR (1950-2099):</label>
                    <input
                      id="card-exp-year"
                      {...register("expiration_year")}
                      type="number"
                      min={1950}
                      max={2099}
                      className="px-2 py-1 text-sm w-20"
                    />
                    {errors.expiration_year && (
                      <p className="text-mainframe-error text-xs mt-1">
                        {errors.expiration_year.message}
                      </p>
                    )}
                  </div>
                </div>

                {/* Optimistic lock version display */}
                <ReadOnlyField label="RECORD VERSION" value={card.updated_at} mono />
              </div>
            </div>

            {/* PF bar */}
            <div className="flex items-center justify-between border-t border-mainframe-border pt-4 text-xs">
              <button
                type="button"
                onClick={() => router.push(`/cards/view?card_number=${card.card_number}`)}
                className="text-mainframe-dim hover:text-mainframe-text"
              >
                PF3=VIEW
              </button>
              <button
                type="button"
                onClick={() => router.push("/cards/list")}
                className="text-mainframe-dim hover:text-mainframe-text"
              >
                PF4=LIST
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2 bg-mainframe-border text-mainframe-text hover:bg-mainframe-panel disabled:opacity-50 text-sm font-bold"
              >
                {saving ? "SAVING..." : "[ PF5=UPDATE ]"}
              </button>
            </div>
          </form>
        )}
      </main>
    </div>
  );
}

function ReadOnlyField({
  label,
  value,
  mono = false,
}: {
  readonly label: string;
  readonly value: string;
  readonly mono?: boolean;
}) {
  return (
    <div className="flex">
      <span className="text-mainframe-dim w-32 shrink-0">{label}:</span>
      <span className={`text-mainframe-dim ${mono ? "font-mono" : ""}`}>{value}</span>
    </div>
  );
}

export default function CardUpdatePage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <CardUpdateContent />
    </Suspense>
  );
}
