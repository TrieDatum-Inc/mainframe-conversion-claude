"use client";

/**
 * Transaction Add Screen — CT02 / COTRN02C equivalent.
 *
 * BMS Map: COTRN02 / COTRN2A (24x80)
 * Implements two-phase flow:
 *   Phase 1 (enter): User fills fields, ENTER → validate → show confirm
 *   Phase 2 (confirm): User enters Y → POST /api/transactions → success message
 *
 * Key business rules from COTRN02C:
 *   - Either acct_id OR card_num must be entered (not both, not neither)
 *   - All data fields mandatory
 *   - Amount format: ±99999999.99
 *   - Date format: YYYY-MM-DD with calendar validation
 *   - Merchant ID must be numeric
 *   - F5=Copy Last Tran: pre-fills data from last existing transaction
 *   - Success: shows new Tran ID in green (mirrors DFHGREEN on ERRMSGC)
 */

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Link from "next/link";
import {
  ApiError,
  copyLastTransaction,
  createTransaction,
  validateTransaction,
} from "@/lib/api";
import type { TransactionDetail, TransactionValidateResponse } from "@/types/transaction";
import ScreenHeader from "@/components/ui/ScreenHeader";
import ErrorMessage from "@/components/ui/ErrorMessage";

// ---------------------------------------------------------------------------
// Zod schema — mirrors COTRN02C VALIDATE-INPUT-DATA-FIELDS
// ---------------------------------------------------------------------------
const amountRegex = /^[+\-]\d{8}\.\d{2}$/;
const dateRegex = /^\d{4}-\d{2}-\d{2}$/;

const transactionSchema = z
  .object({
    acct_id: z.string().max(11).optional().or(z.literal("")),
    card_num: z.string().max(16).optional().or(z.literal("")),
    tran_type_cd: z.string().min(1, "Type CD can NOT be empty").max(2).regex(/^\d+$/, "Type CD must be Numeric"),
    tran_cat_cd: z.string().min(1, "Category CD can NOT be empty").max(4).regex(/^\d+$/, "Category CD must be Numeric"),
    tran_source: z.string().min(1, "Source can NOT be empty").max(10),
    tran_desc: z.string().min(1, "Description can NOT be empty").max(100),
    tran_amt: z
      .string()
      .min(1, "Amount can NOT be empty")
      .regex(amountRegex, "Amount should be in format -99999999.99"),
    tran_orig_dt: z
      .string()
      .min(1, "Orig Date can NOT be empty")
      .regex(dateRegex, "Orig Date should be in format YYYY-MM-DD")
      .refine((d) => !isNaN(Date.parse(d)), "Orig Date - Not a valid date"),
    tran_proc_dt: z
      .string()
      .min(1, "Proc Date can NOT be empty")
      .regex(dateRegex, "Proc Date should be in format YYYY-MM-DD")
      .refine((d) => !isNaN(Date.parse(d)), "Proc Date - Not a valid date"),
    tran_merchant_id: z
      .string()
      .min(1, "Merchant ID can NOT be empty")
      .max(9)
      .regex(/^\d+$/, "Merchant ID must be Numeric"),
    tran_merchant_name: z.string().min(1, "Merchant Name can NOT be empty").max(50),
    tran_merchant_city: z.string().min(1, "Merchant City can NOT be empty").max(50),
    tran_merchant_zip: z.string().min(1, "Merchant Zip can NOT be empty").max(10),
  })
  .refine(
    (d) => (d.acct_id && d.acct_id.trim()) || (d.card_num && d.card_num.trim()),
    { message: "Account or Card Number must be entered", path: ["acct_id"] }
  );

type FormValues = z.infer<typeof transactionSchema>;

type ScreenPhase = "enter" | "confirm" | "success";

export default function TransactionAddScreen() {
  const [phase, setPhase] = useState<ScreenPhase>("enter");
  const [confirmInput, setConfirmInput] = useState("");
  const [validationResult, setValidationResult] = useState<TransactionValidateResponse | null>(null);
  const [createdTran, setCreatedTran] = useState<TransactionDetail | null>(null);
  const [message, setMessage] = useState<{ text: string; type: "error" | "success" | "info" } | null>(null);
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    getValues,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(transactionSchema),
    defaultValues: {
      tran_type_cd: "",
      tran_cat_cd: "",
      tran_source: "",
      tran_desc: "",
      tran_amt: "",
      tran_orig_dt: "",
      tran_proc_dt: "",
      tran_merchant_id: "",
      tran_merchant_name: "",
      tran_merchant_city: "",
      tran_merchant_zip: "",
    },
  });

  // ENTER handler — Phase 1: validate then show confirm
  const onSubmitEnter = async (data: FormValues) => {
    setLoading(true);
    setMessage(null);
    try {
      const result = await validateTransaction({
        acct_id: data.acct_id || undefined,
        card_num: data.card_num || undefined,
        tran_type_cd: data.tran_type_cd,
        tran_cat_cd: data.tran_cat_cd,
        tran_source: data.tran_source,
        tran_desc: data.tran_desc,
        tran_amt: data.tran_amt,
        tran_orig_dt: data.tran_orig_dt,
        tran_proc_dt: data.tran_proc_dt,
        tran_merchant_id: data.tran_merchant_id,
        tran_merchant_name: data.tran_merchant_name,
        tran_merchant_city: data.tran_merchant_city,
        tran_merchant_zip: data.tran_merchant_zip,
      });
      setValidationResult(result);
      setPhase("confirm");
      setMessage({ text: "You are about to add this transaction. Please confirm:", type: "info" });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Validation failed";
      setMessage({ text: msg, type: "error" });
    } finally {
      setLoading(false);
    }
  };

  // Confirm handler — Phase 2: create or reject
  const handleConfirm = async () => {
    if (!confirmInput.trim()) {
      setMessage({ text: "Confirm to add this transaction", type: "error" });
      return;
    }
    if (confirmInput.toUpperCase() !== "Y" && confirmInput.toUpperCase() !== "N") {
      setMessage({ text: "Invalid value. Valid values are (Y/N)", type: "error" });
      return;
    }
    if (confirmInput.toUpperCase() === "N") {
      setMessage({ text: "Confirm to add this transaction", type: "error" });
      return;
    }

    setLoading(true);
    setMessage(null);
    try {
      const formData = getValues();
      const tran = await createTransaction({
        acct_id: formData.acct_id || undefined,
        card_num: formData.card_num || undefined,
        tran_type_cd: formData.tran_type_cd,
        tran_cat_cd: formData.tran_cat_cd,
        tran_source: formData.tran_source,
        tran_desc: formData.tran_desc,
        tran_amt: formData.tran_amt,
        tran_orig_dt: formData.tran_orig_dt,
        tran_proc_dt: formData.tran_proc_dt,
        tran_merchant_id: formData.tran_merchant_id,
        tran_merchant_name: formData.tran_merchant_name,
        tran_merchant_city: formData.tran_merchant_city,
        tran_merchant_zip: formData.tran_merchant_zip,
        confirm: "Y",
      });
      setCreatedTran(tran);
      setPhase("success");
      // DFHGREEN success message — mirrors WRITE-TRANSACT-FILE success path
      setMessage({
        text: `Transaction added successfully. Your Tran ID is ${tran.tran_id}`,
        type: "success",
      });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Unable to Add Transaction";
      setMessage({ text: msg, type: "error" });
      setPhase("enter");
    } finally {
      setLoading(false);
    }
  };

  // F5: Copy last transaction — mirrors COPY-LAST-TRAN-DATA
  const handleCopyLast = async () => {
    const formData = getValues();
    const cardNum = formData.card_num?.trim();
    const acctId = formData.acct_id?.trim();
    if (!cardNum && !acctId) {
      setMessage({ text: "Account or Card Number must be entered before copying", type: "error" });
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      const last = await copyLastTransaction({ card_num: cardNum, acct_id: acctId });
      setValue("tran_type_cd", last.tran_type_cd.trim());
      setValue("tran_cat_cd", last.tran_cat_cd.trim());
      setValue("tran_source", last.tran_source.trim());
      setValue("tran_desc", last.tran_desc.trim());
      setValue("tran_amt", String(last.tran_amt));
      setValue("tran_merchant_id", last.tran_merchant_id.trim());
      setValue("tran_merchant_name", last.tran_merchant_name.trim());
      setValue("tran_merchant_city", last.tran_merchant_city.trim());
      setValue("tran_merchant_zip", last.tran_merchant_zip.trim());
      setMessage({ text: "Data copied from last transaction", type: "info" });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Unable to copy last transaction";
      setMessage({ text: msg, type: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    reset();
    setPhase("enter");
    setMessage(null);
    setValidationResult(null);
    setConfirmInput("");
  };

  const firstError = Object.values(errors)[0]?.message;

  return (
    <div className="screen-container min-h-screen flex flex-col">
      <ScreenHeader tranId="CT02" pgmName="COTRN02C" title="Add Transaction" />

      <form onSubmit={handleSubmit(onSubmitEnter)} className="flex-1 flex flex-col">
        {/* Key entry area — Row 6 */}
        <div className="px-4 py-3 border-b border-gray-800">
          <div className="flex items-center gap-6 flex-wrap text-xs">
            <div className="flex items-center gap-2">
              <label className="field-label whitespace-nowrap">Enter Acct #:</label>
              <input
                {...register("acct_id")}
                type="text"
                maxLength={11}
                className="input-field w-28"
                placeholder="11 digits"
                aria-label="Account ID"
              />
            </div>
            <span className="text-gray-400">(or)</span>
            <div className="flex items-center gap-2">
              <label className="field-label whitespace-nowrap">Card #:</label>
              <input
                {...register("card_num")}
                type="text"
                maxLength={16}
                className="input-field w-40"
                placeholder="16 digits"
                aria-label="Card Number"
              />
            </div>
          </div>
          {errors.acct_id && (
            <p className="text-red-400 text-xs mt-1">{errors.acct_id.message}</p>
          )}
        </div>

        {/* Separator — Row 8 */}
        <div className="px-4 my-2">
          <div className="border-b border-gray-600 border-dashed" />
        </div>

        {/* Transaction data entry — Rows 10-18 */}
        <div className="px-4 space-y-3 text-xs flex-1">
          {/* Row 10: Type CD + Category CD + Source */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="field-label block mb-1">Type Code:</label>
              <input
                {...register("tran_type_cd")}
                type="text"
                maxLength={2}
                className={`input-field ${errors.tran_type_cd ? "input-field-error" : ""}`}
                placeholder="e.g. 01"
              />
              {errors.tran_type_cd && (
                <p className="text-red-400 text-xs mt-0.5">{errors.tran_type_cd.message}</p>
              )}
            </div>
            <div>
              <label className="field-label block mb-1">Category Code:</label>
              <input
                {...register("tran_cat_cd")}
                type="text"
                maxLength={4}
                className={`input-field ${errors.tran_cat_cd ? "input-field-error" : ""}`}
                placeholder="e.g. 0001"
              />
              {errors.tran_cat_cd && (
                <p className="text-red-400 text-xs mt-0.5">{errors.tran_cat_cd.message}</p>
              )}
            </div>
            <div>
              <label className="field-label block mb-1">Source:</label>
              <input
                {...register("tran_source")}
                type="text"
                maxLength={10}
                className={`input-field ${errors.tran_source ? "input-field-error" : ""}`}
                placeholder="e.g. ONLINE"
              />
              {errors.tran_source && (
                <p className="text-red-400 text-xs mt-0.5">{errors.tran_source.message}</p>
              )}
            </div>
          </div>

          {/* Row 12: Description */}
          <div>
            <label className="field-label block mb-1">Description:</label>
            <input
              {...register("tran_desc")}
              type="text"
              maxLength={100}
              className={`input-field ${errors.tran_desc ? "input-field-error" : ""}`}
              placeholder="Transaction description"
            />
            {errors.tran_desc && (
              <p className="text-red-400 text-xs mt-0.5">{errors.tran_desc.message}</p>
            )}
          </div>

          {/* Row 14: Amount + Orig Date + Proc Date */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="field-label block mb-1">Amount:</label>
              <input
                {...register("tran_amt")}
                type="text"
                maxLength={12}
                className={`input-field font-mono ${errors.tran_amt ? "input-field-error" : ""}`}
                placeholder="-99999999.99"
              />
              <p className="text-blue-400 text-xs">(-99999999.99)</p>
              {errors.tran_amt && (
                <p className="text-red-400 text-xs">{errors.tran_amt.message}</p>
              )}
            </div>
            <div>
              <label className="field-label block mb-1">Orig Date:</label>
              <input
                {...register("tran_orig_dt")}
                type="text"
                maxLength={10}
                className={`input-field ${errors.tran_orig_dt ? "input-field-error" : ""}`}
                placeholder="YYYY-MM-DD"
              />
              <p className="text-blue-400 text-xs">(YYYY-MM-DD)</p>
              {errors.tran_orig_dt && (
                <p className="text-red-400 text-xs">{errors.tran_orig_dt.message}</p>
              )}
            </div>
            <div>
              <label className="field-label block mb-1">Proc Date:</label>
              <input
                {...register("tran_proc_dt")}
                type="text"
                maxLength={10}
                className={`input-field ${errors.tran_proc_dt ? "input-field-error" : ""}`}
                placeholder="YYYY-MM-DD"
              />
              <p className="text-blue-400 text-xs">(YYYY-MM-DD)</p>
              {errors.tran_proc_dt && (
                <p className="text-red-400 text-xs">{errors.tran_proc_dt.message}</p>
              )}
            </div>
          </div>

          {/* Row 16: Merchant ID + Merchant Name */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="field-label block mb-1">Merchant ID:</label>
              <input
                {...register("tran_merchant_id")}
                type="text"
                maxLength={9}
                className={`input-field ${errors.tran_merchant_id ? "input-field-error" : ""}`}
                placeholder="9 digits"
              />
              {errors.tran_merchant_id && (
                <p className="text-red-400 text-xs mt-0.5">{errors.tran_merchant_id.message}</p>
              )}
            </div>
            <div>
              <label className="field-label block mb-1">Merchant Name:</label>
              <input
                {...register("tran_merchant_name")}
                type="text"
                maxLength={50}
                className={`input-field ${errors.tran_merchant_name ? "input-field-error" : ""}`}
                placeholder="Merchant name"
              />
              {errors.tran_merchant_name && (
                <p className="text-red-400 text-xs mt-0.5">{errors.tran_merchant_name.message}</p>
              )}
            </div>
          </div>

          {/* Row 18: Merchant City + ZIP */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="field-label block mb-1">Merchant City:</label>
              <input
                {...register("tran_merchant_city")}
                type="text"
                maxLength={50}
                className={`input-field ${errors.tran_merchant_city ? "input-field-error" : ""}`}
                placeholder="City"
              />
              {errors.tran_merchant_city && (
                <p className="text-red-400 text-xs mt-0.5">{errors.tran_merchant_city.message}</p>
              )}
            </div>
            <div>
              <label className="field-label block mb-1">Merchant Zip:</label>
              <input
                {...register("tran_merchant_zip")}
                type="text"
                maxLength={10}
                className={`input-field ${errors.tran_merchant_zip ? "input-field-error" : ""}`}
                placeholder="ZIP code"
              />
              {errors.tran_merchant_zip && (
                <p className="text-red-400 text-xs mt-0.5">{errors.tran_merchant_zip.message}</p>
              )}
            </div>
          </div>

          {/* Row 21 — Confirmation area (shown in confirm phase) */}
          {phase === "confirm" && (
            <div className="border-t border-gray-700 pt-3">
              <div className="flex items-center gap-3">
                <span className="text-teal-400 text-xs">
                  You are about to add this transaction. Please confirm:
                </span>
                <input
                  type="text"
                  value={confirmInput}
                  onChange={(e) => setConfirmInput(e.target.value)}
                  maxLength={1}
                  className="input-field w-10 text-center uppercase"
                  aria-label="Confirm Y or N"
                  autoFocus
                />
                <span className="text-gray-400 text-xs">(Y/N)</span>
                <button
                  type="button"
                  onClick={() => void handleConfirm()}
                  className="btn-primary"
                  disabled={loading}
                >
                  Confirm
                </button>
                <button
                  type="button"
                  onClick={() => { setPhase("enter"); setMessage(null); }}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
              {/* Show validation result details */}
              {validationResult && (
                <div className="mt-2 text-xs text-gray-400 space-y-0.5">
                  <div>Resolved Card: <span className="text-blue-300">{validationResult.resolved_card_num}</span></div>
                  <div>Account: <span className="text-blue-300">{validationResult.resolved_acct_id}</span></div>
                  <div>Amount: <span className="text-green-300 font-mono">{validationResult.normalized_amt}</span></div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Action buttons */}
        {phase === "enter" && (
          <div className="px-4 py-2 flex gap-2 border-t border-gray-800 text-xs">
            <button type="submit" className="btn-primary" disabled={loading}>
              ENTER Continue
            </button>
            <button
              type="button"
              onClick={() => void handleCopyLast()}
              className="btn-secondary"
              disabled={loading}
            >
              F5 Copy Last Tran.
            </button>
            <button type="button" onClick={handleClear} className="btn-secondary">
              F4 Clear
            </button>
            <Link href="/" className="btn-secondary">
              F3 Back
            </Link>
          </div>
        )}

        {/* Row 23 — ERRMSG */}
        <div className="px-4 pb-2">
          {firstError && phase === "enter" && (
            <ErrorMessage message={firstError} variant="error" />
          )}
          <ErrorMessage
            message={message?.text ?? null}
            variant={message?.type ?? "error"}
          />
        </div>
      </form>

      {/* Row 24 — PF key legend */}
      <div className="px-4 py-1.5 bg-gray-950 border-t border-gray-700 text-xs text-yellow-400 font-mono">
        ENTER=Continue &nbsp; F3=Back &nbsp; F4=Clear &nbsp; F5=Copy Last Tran.
      </div>
    </div>
  );
}
