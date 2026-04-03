"use client";
/**
 * COCRDLIC (Transaction CCLI) — Credit Card List Screen
 * BMS Map: COCRDLI / CCRDLIA
 * Paginated browse with account/card filters and View/Edit row actions.
 */
import { useRef, useState } from "react";
import { FunctionKeyBar } from "@/components/ui/FunctionKeyBar";
import { MessageBar } from "@/components/ui/MessageBar";
import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { useCardList } from "@/hooks/useCardList";
import type { CardListItem } from "@/types/card";

interface CardListScreenProps { onViewCard: (item: CardListItem) => void; onEditCard: (item: CardListItem) => void; }

function validateFilters(acctId: string, cardNumFilter: string): string | null {
  if (acctId.trim() && !/^\d{11}$/.test(acctId.trim())) return "ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER";
  if (cardNumFilter.trim() && !/^\d{16}$/.test(cardNumFilter.trim())) return "CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER";
  return null;
}

export function CardListScreen({ onViewCard, onEditCard }: CardListScreenProps) {
  const { data, isLoading, error, page, goNextPage, goPrevPage, applyFilters, canGoBack, canGoForward } = useCardList(7);
  const [acctIdInput, setAcctIdInput] = useState("");
  const [cardNumInput, setCardNumInput] = useState("");
  const [filterError, setFilterError] = useState<string | null>(null);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const err = validateFilters(acctIdInput, cardNumInput);
    if (err) { setFilterError(err); return; }
    setFilterError(null);
    applyFilters(acctIdInput, cardNumInput);
  };

  const infoMessage = isLoading ? "Loading..." : data?.total_on_page === 0 ? "NO RECORDS FOUND" : !canGoForward && data?.total_on_page ? "NO MORE PAGES TO DISPLAY" : "CLICK VIEW TO SEE DETAILS, EDIT TO UPDATE A RECORD";

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col font-mono">
      <ScreenHeader tranName="CCLI" pgmName="COCRDLIC" title1="AWS CardDemo - Credit Card Management" title2="Credit Card List" />
      <div className="px-4 py-2 text-center"><span className="text-white font-bold">List Credit Cards</span><span className="ml-auto float-right text-blue-300 text-sm">Page {page}</span></div>
      <form onSubmit={handleFilterSubmit} className="px-4 py-2 space-y-1">
        <div className="flex items-center gap-2 text-sm">
          <label className="text-cyan-300 w-44 text-right shrink-0">Account Number Filter :</label>
          <input type="text" value={acctIdInput} onChange={(e) => setAcctIdInput(e.target.value)} maxLength={11} placeholder="11 digits" className="bg-gray-900 text-green-300 border-b border-green-500 underline focus:outline-none px-1 py-0.5 w-32" aria-label="Account number filter" autoFocus />
        </div>
        <div className="flex items-center gap-2 text-sm">
          <label className="text-cyan-300 w-44 text-right shrink-0">Card Number Filter :</label>
          <input type="text" value={cardNumInput} onChange={(e) => setCardNumInput(e.target.value)} maxLength={16} placeholder="16 digits" className="bg-gray-900 text-green-300 border-b border-green-500 underline focus:outline-none px-1 py-0.5 w-44" aria-label="Card number filter" />
          <button type="submit" className="ml-2 px-3 py-0.5 bg-blue-800 text-white rounded hover:bg-blue-700 text-xs">Apply Filter</button>
        </div>
        {filterError && <p className="text-red-400 text-xs ml-48">{filterError}</p>}
      </form>
      <div className="px-4 py-1">
        <div className="grid grid-cols-[3rem_14rem_20rem_6rem_12rem] gap-2 text-sm text-yellow-300 font-bold border-b border-gray-600 pb-1">
          <span></span><span>Account Number</span><span>Card Number</span><span>Active</span><span>Actions</span>
        </div>
      </div>
      <div className="px-4 flex-1">
        {isLoading ? <div className="text-gray-400 text-sm py-4 text-center">Loading...</div> : (
          <div className="space-y-0.5">
            {data?.items.map((item, idx) => (
              <div key={item.card_num} className="grid grid-cols-[3rem_14rem_20rem_6rem_12rem] gap-2 items-center text-sm py-0.5 hover:bg-gray-800 rounded">
                <span className="text-gray-500 text-xs">{idx + 1}</span>
                <span className="text-white">{item.card_acct_id}</span>
                <span className="text-white tracking-widest">{item.card_num}</span>
                <span className={item.card_active_status === "Y" ? "text-green-400" : "text-red-400"}>{item.card_active_status}</span>
                <div className="flex gap-1">
                  <button onClick={() => onViewCard(item)} className="px-2 py-0.5 text-xs bg-blue-800 text-white rounded hover:bg-blue-700" aria-label={`View card ${item.card_num}`}>View</button>
                  <button onClick={() => onEditCard(item)} className="px-2 py-0.5 text-xs bg-yellow-700 text-white rounded hover:bg-yellow-600" aria-label={`Edit card ${item.card_num}`}>Edit</button>
                </div>
              </div>
            ))}
            {Array.from({ length: Math.max(0, 7 - (data?.items.length ?? 0)) }).map((_, i) => (
              <div key={`empty-${i}`} className="grid grid-cols-[3rem_14rem_20rem_6rem_12rem] gap-2 py-0.5">
                <span className="text-gray-700 text-xs">{(data?.items.length ?? 0) + i + 1}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="px-4 py-1"><MessageBar message={error ?? infoMessage} type={error ? "error" : "info"} /></div>
      <FunctionKeyBar keys={[
        { label: "F3=Exit", action: () => window.location.assign("/") },
        { label: "F7=Backward", action: goPrevPage, disabled: !canGoBack },
        { label: "F8=Forward", action: goNextPage, disabled: !canGoForward },
      ]} />
    </div>
  );
}
