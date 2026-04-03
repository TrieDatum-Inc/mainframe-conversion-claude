"use client";
/**
 * COCRDUPC (Transaction CCUP) — Credit Card Update Screen
 * BMS Map: COCRDUP / CCRDUPA
 * 6-state machine: NOT_FETCHED → SHOW_DETAILS → CHANGES_NOT_OK | OK_NOT_CONFIRMED → DONE/FAILED
 * Optimistic concurrency via updated_at token. Expiry day hidden/non-editable.
 */
import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { FormField } from "@/components/ui/FormField";
import { FunctionKeyBar } from "@/components/ui/FunctionKeyBar";
import { MessageBar } from "@/components/ui/MessageBar";
import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { ApiClientError, fetchCardDetail, updateCard } from "@/lib/api";
import type { CardDetail, CardUpdateRequest } from "@/types/card";

type UpdatePhase = "NOT_FETCHED" | "SHOW_DETAILS" | "CHANGES_NOT_OK" | "OK_NOT_CONFIRMED" | "DONE" | "LOCK_ERROR" | "FAILED";
interface UpdateFormValues { card_embossed_name: string; card_active_status: string; expiry_month: string; expiry_year: string; }

function validateName(v: string): string | undefined { if (!v.trim()) return "Card name not provided"; if (!/^[A-Za-z ]+$/.test(v.trim())) return "Card name can only contain alphabets and spaces"; return undefined; }
function validateStatus(v: string): string | undefined { if (!["Y","N","y","n"].includes(v)) return "Card Active Status must be Y or N"; return undefined; }
function validateMonth(v: string): string | undefined { const n = Number(v); if (!v.trim() || isNaN(n) || n < 1 || n > 12) return "Card expiry month must be between 1 and 12"; return undefined; }
function validateYear(v: string): string | undefined { const n = Number(v); if (!v.trim() || isNaN(n) || n < 1950 || n > 2099) return "Invalid card expiry year"; return undefined; }

interface CardUpdateScreenProps { preloadedCardNum?: string; preloadedAcctId?: string; onBack: () => void; }

export function CardUpdateScreen({ preloadedCardNum, preloadedAcctId, onBack }: CardUpdateScreenProps) {
  const [phase, setPhase] = useState<UpdatePhase>("NOT_FETCHED");
  const [searchAcctId, setSearchAcctId] = useState(preloadedAcctId ?? "");
  const [searchCardNum, setSearchCardNum] = useState(preloadedCardNum ?? "");
  const [searchError, setSearchError] = useState<string | null>(null);
  const [currentDetail, setCurrentDetail] = useState<CardDetail | null>(null);
  const [infoMsg, setInfoMsg] = useState("Please enter Account and Card Number");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register, handleSubmit, formState: { errors }, setValue, getValues, reset, trigger } = useForm<UpdateFormValues>({ mode: "onSubmit" });

  const loadCard = useCallback(async (cardNum: string) => {
    setErrorMsg(null);
    try {
      const detail = await fetchCardDetail(cardNum);
      setCurrentDetail(detail);
      setValue("card_embossed_name", detail.card_embossed_name ?? "");
      setValue("card_active_status", detail.card_active_status);
      setValue("expiry_month", String(detail.expiry_month ?? ""));
      setValue("expiry_year", String(detail.expiry_year ?? ""));
      setPhase("SHOW_DETAILS"); setInfoMsg("Details of selected card shown above");
    } catch (err) { setErrorMsg(err instanceof Error ? err.message : "Card not found"); }
  }, [setValue]);

  useEffect(() => { if (preloadedCardNum) loadCard(preloadedCardNum); }, [preloadedCardNum, loadCard]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!/^\d{11}$/.test(searchAcctId.trim())) { setSearchError("ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER"); return; }
    if (!/^\d{16}$/.test(searchCardNum.trim())) { setSearchError("CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER"); return; }
    setSearchError(null);
    await loadCard(searchCardNum.trim());
  };

  const handleValidate = async (e: React.FormEvent) => {
    e.preventDefault();
    const valid = await trigger();
    if (!valid) { setPhase("CHANGES_NOT_OK"); setInfoMsg("Update card details presented above."); return; }
    setPhase("OK_NOT_CONFIRMED"); setInfoMsg("Changes validated.Press F5 to save"); setErrorMsg(null);
  };

  const handleSave = async () => {
    if (!currentDetail || phase !== "OK_NOT_CONFIRMED") return;
    setIsSubmitting(true);
    const values = getValues();
    const payload: CardUpdateRequest = { card_embossed_name: values.card_embossed_name.trim().toUpperCase(), card_active_status: values.card_active_status.toUpperCase() as "Y"|"N", expiry_month: Number(values.expiry_month), expiry_year: Number(values.expiry_year), updated_at: currentDetail.updated_at };
    try {
      await updateCard(currentDetail.card_num, payload);
      setPhase("DONE"); setInfoMsg("Changes committed to database"); setErrorMsg(null);
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 409) { setErrorMsg("Record was changed by another user. Refreshing..."); await loadCard(currentDetail.card_num); return; }
        if (err.status === 503) { setPhase("LOCK_ERROR"); setInfoMsg("Changes unsuccessful. Please try again"); setErrorMsg(err.message); return; }
      }
      setPhase("FAILED"); setInfoMsg("Changes unsuccessful. Please try again"); setErrorMsg(err instanceof Error ? err.message : "Update failed");
    } finally { setIsSubmitting(false); }
  };

  const handleCancel = async () => { if (currentDetail) await loadCard(currentDetail.card_num); else { reset(); setPhase("NOT_FETCHED"); setInfoMsg("Please enter Account and Card Number"); } };
  const handleReset = () => { setPhase("NOT_FETCHED"); setCurrentDetail(null); setSearchAcctId(""); setSearchCardNum(""); reset(); setInfoMsg("Please enter Account and Card Number"); setErrorMsg(null); };

  const searchFieldsEditable = phase === "NOT_FETCHED" || phase === "DONE" || phase === "LOCK_ERROR" || phase === "FAILED";
  const editFieldsEditable = phase === "SHOW_DETAILS" || phase === "CHANGES_NOT_OK";
  const confirmPhase = phase === "OK_NOT_CONFIRMED";

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col font-mono">
      <ScreenHeader tranName="CCUP" pgmName="COCRDUPC" title1="AWS CardDemo - Credit Card Management" title2="Update Credit Card Details" />
      <div className="px-4 py-2 text-center text-white font-bold">Update Credit Card Details</div>
      <div className="px-4 py-2 space-y-2">
        {searchFieldsEditable ? (
          <form onSubmit={handleSearch} className="space-y-2">
            <FormField id="search-acct" label="Account Number" value={searchAcctId} onChange={(e) => setSearchAcctId(e.target.value)} maxLength={11} placeholder="11 digits" autoFocus />
            <FormField id="search-card" label="Card Number" value={searchCardNum} onChange={(e) => setSearchCardNum(e.target.value)} maxLength={16} placeholder="16 digits" />
            {searchError && <p className="text-red-400 text-xs ml-56">{searchError}</p>}
            <div className="ml-56"><button type="submit" className="px-4 py-1 bg-blue-800 text-white rounded hover:bg-blue-700 text-sm">ENTER=Process</button></div>
          </form>
        ) : (
          <div className="space-y-2">
            <FormField id="search-acct" label="Account Number" value={currentDetail?.card_acct_id ?? searchAcctId} protected />
            <FormField id="search-card" label="Card Number" value={currentDetail?.card_num ?? searchCardNum} protected />
          </div>
        )}
      </div>
      {currentDetail && phase !== "NOT_FETCHED" && (
        <form onSubmit={handleValidate} className="px-4 py-2 space-y-3 border-t border-gray-700">
          {editFieldsEditable ? (
            <FormField id="crdname" label="Name on card" {...register("card_embossed_name", { validate: validateName })} error={errors.card_embossed_name?.message} maxLength={50} placeholder="Alphabetic characters and spaces only" className="w-96" />
          ) : <FormField id="crdname" label="Name on card" value={getValues("card_embossed_name")} protected />}
          {editFieldsEditable ? (
            <FormField id="crdstcd" label="Card Active Y/N" {...register("card_active_status", { validate: validateStatus })} error={errors.card_active_status?.message} maxLength={1} placeholder="Y or N" className="w-10 uppercase" />
          ) : <FormField id="crdstcd" label="Card Active Y/N" value={getValues("card_active_status")} protected />}
          <div className="flex items-center gap-2 text-sm">
            <span className="text-cyan-300 w-52 text-right">Expiry Date :</span>
            {editFieldsEditable ? (
              <div className="flex items-center gap-1">
                <input {...register("expiry_month", { validate: validateMonth })} className={`bg-gray-900 text-green-300 border-b border-green-500 underline focus:outline-none px-1 py-0.5 w-12 text-right ${errors.expiry_month ? "border-red-500 text-red-300" : ""}`} maxLength={2} placeholder="MM" aria-label="Expiry month" />
                <span className="text-white">/</span>
                <input {...register("expiry_year", { validate: validateYear })} className={`bg-gray-900 text-green-300 border-b border-green-500 underline focus:outline-none px-1 py-0.5 w-16 text-right ${errors.expiry_year ? "border-red-500 text-red-300" : ""}`} maxLength={4} placeholder="YYYY" aria-label="Expiry year" />
                {(errors.expiry_month || errors.expiry_year) && <span className="text-red-400 text-xs">{errors.expiry_month?.message || errors.expiry_year?.message}</span>}
              </div>
            ) : <span className="text-white border-b border-gray-600 px-1">{getValues("expiry_month")?.padStart(2,"0")}/{getValues("expiry_year")}</span>}
          </div>
          <FormField id="cvv" label="CVV" value={currentDetail.card_cvv_cd ?? ""} protected />
          {editFieldsEditable && <div className="ml-56"><button type="submit" className="px-4 py-1 bg-blue-800 text-white rounded hover:bg-blue-700 text-sm">ENTER=Validate Changes</button></div>}
        </form>
      )}
      {(phase === "DONE" || phase === "LOCK_ERROR" || phase === "FAILED") && <div className="px-4 py-2 ml-56"><button onClick={handleReset} className="px-4 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 text-sm">New Search</button></div>}
      <div className="px-4 py-2 mt-auto"><MessageBar message={infoMsg} type={phase === "DONE" ? "success" : "info"} /></div>
      {errorMsg && <div className="px-4 pb-1"><MessageBar message={errorMsg} type="error" /></div>}
      <FunctionKeyBar keys={[
        { label: "ENTER=Process", action: () => {} },
        { label: "F3=Exit", action: onBack },
        { label: "F5=Save", action: handleSave, highlighted: confirmPhase, disabled: phase !== "OK_NOT_CONFIRMED" || isSubmitting },
        { label: "F12=Cancel", action: handleCancel, disabled: phase === "NOT_FETCHED" },
      ]} />
    </div>
  );
}
