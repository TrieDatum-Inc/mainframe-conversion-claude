"use client";
/**
 * COCRDSLC (Transaction CCDL) — Credit Card Detail View Screen
 * BMS Map: COCRDSL / CCRDSLA
 * Direct entry or pre-populated from COCRDLIC. Read-only display.
 */
import { useCallback, useEffect, useState } from "react";
import { FormField } from "@/components/ui/FormField";
import { FunctionKeyBar } from "@/components/ui/FunctionKeyBar";
import { MessageBar } from "@/components/ui/MessageBar";
import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { fetchCardDetail } from "@/lib/api";
import { formatExpiry } from "@/lib/utils";
import type { CardDetail } from "@/types/card";

interface CardDetailScreenProps { preloadedCardNum?: string; preloadedAcctId?: string; onBack: () => void; onEditCard?: (detail: CardDetail) => void; }

function validateAcctId(v: string): string | null {
  if (!v.trim()) return "Account number not provided";
  if (!/^\d{11}$/.test(v.trim())) return "ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER";
  return null;
}
function validateCardNum(v: string): string | null {
  if (!v.trim()) return "Card number not provided";
  if (!/^\d{16}$/.test(v.trim())) return "CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER";
  return null;
}

export function CardDetailScreen({ preloadedCardNum, preloadedAcctId, onBack, onEditCard }: CardDetailScreenProps) {
  const isPreloaded = Boolean(preloadedCardNum);
  const [acctId, setAcctId] = useState(preloadedAcctId ?? "");
  const [cardNum, setCardNum] = useState(preloadedCardNum ?? "");
  const [acctError, setAcctError] = useState<string | null>(null);
  const [cardError, setCardError] = useState<string | null>(null);
  const [detail, setDetail] = useState<CardDetail | null>(null);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadCard = useCallback(async (num: string) => {
    setIsLoading(true); setErrorMsg(null);
    try {
      const result = await fetchCardDetail(num);
      setDetail(result); setInfoMsg("Displaying requested details");
    } catch (err) {
      setDetail(null); setErrorMsg(err instanceof Error ? err.message : "Error loading card"); setInfoMsg(null);
    } finally { setIsLoading(false); }
  }, []);

  useEffect(() => { if (preloadedCardNum) loadCard(preloadedCardNum); }, [preloadedCardNum, loadCard]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const ae = validateAcctId(acctId), ce = validateCardNum(cardNum);
    setAcctError(ae); setCardError(ce);
    if (ae || ce) return;
    await loadCard(cardNum.trim());
  };

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col font-mono">
      <ScreenHeader tranName="CCDL" pgmName="COCRDSLC" title1="AWS CardDemo - Credit Card Management" title2="Credit Card Detail View" />
      <div className="px-4 py-2 text-center text-white font-bold">View Credit Card Detail</div>
      <form onSubmit={handleSearch} className="px-4 py-3 space-y-2">
        <FormField id="acct-id" label="Account Number" value={acctId} onChange={(e) => setAcctId(e.target.value)} maxLength={11} placeholder="11 digits" protected={isPreloaded} error={acctError ?? undefined} autoFocus={!isPreloaded} hint="(11 digits)" />
        <FormField id="card-num" label="Card Number" value={cardNum} onChange={(e) => setCardNum(e.target.value)} maxLength={16} placeholder="16 digits" protected={isPreloaded} error={cardError ?? undefined} hint="(16 digits)" />
        {!isPreloaded && <div className="ml-56"><button type="submit" disabled={isLoading} className="px-4 py-1 bg-blue-800 text-white rounded hover:bg-blue-700 text-sm disabled:opacity-50">{isLoading ? "Searching..." : "ENTER=Search Cards"}</button></div>}
      </form>
      {detail && (
        <div className="px-4 py-2 space-y-3 border-t border-gray-700 mt-2">
          <div className="flex items-center gap-2 text-sm"><span className="text-cyan-300 w-52 text-right">Name on card :</span><span className="text-white border-b border-gray-600 min-w-64 px-1">{detail.card_embossed_name ?? "—"}</span></div>
          <div className="flex items-center gap-2 text-sm"><span className="text-cyan-300 w-52 text-right">Card Active Y/N :</span><span className={`border-b border-gray-600 px-2 font-bold ${detail.card_active_status === "Y" ? "text-green-400" : "text-red-400"}`}>{detail.card_active_status}</span></div>
          <div className="flex items-center gap-2 text-sm"><span className="text-cyan-300 w-52 text-right">Expiry Date :</span><span className="text-white border-b border-gray-600 px-1">{formatExpiry(detail.expiry_month, detail.expiry_year)}</span></div>
          <div className="flex items-center gap-2 text-sm"><span className="text-cyan-300 w-52 text-right">CVV :</span><span className="text-white border-b border-gray-600 px-1">{detail.card_cvv_cd ?? "—"}</span></div>
          {onEditCard && <div className="ml-56 pt-2"><button onClick={() => onEditCard(detail)} className="px-4 py-1 bg-yellow-700 text-white rounded hover:bg-yellow-600 text-sm">Edit This Card</button></div>}
        </div>
      )}
      <div className="px-4 py-2 mt-auto"><MessageBar message={infoMsg} type="info" /></div>
      {errorMsg && <div className="px-4 pb-1"><MessageBar message={errorMsg} type="error" /></div>}
      <FunctionKeyBar keys={[{ label: "ENTER=Search Cards", action: handleSearch }, { label: "F3=Exit", action: onBack }]} />
    </div>
  );
}
