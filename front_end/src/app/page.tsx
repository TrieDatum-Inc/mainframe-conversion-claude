"use client";
import { useState } from "react";
import { CardDetailScreen } from "@/components/forms/CardDetailScreen";
import { CardListScreen } from "@/components/forms/CardListScreen";
import { CardUpdateScreen } from "@/components/forms/CardUpdateScreen";
import type { CardDetail, CardListItem } from "@/types/card";

type Screen = "list" | "detail" | "update";
interface NavState { screen: Screen; cardNum?: string; acctId?: string; }

export default function Home() {
  const [nav, setNav] = useState<NavState>({ screen: "list" });
  const goToDetail = (item: CardListItem) => setNav({ screen: "detail", cardNum: item.card_num, acctId: item.card_acct_id });
  const goToEdit = (item: CardListItem | CardDetail) => setNav({ screen: "update", cardNum: item.card_num, acctId: item.card_acct_id });
  const goToList = () => setNav({ screen: "list" });

  if (nav.screen === "detail") return <CardDetailScreen preloadedCardNum={nav.cardNum} preloadedAcctId={nav.acctId} onBack={goToList} onEditCard={goToEdit} />;
  if (nav.screen === "update") return <CardUpdateScreen preloadedCardNum={nav.cardNum} preloadedAcctId={nav.acctId} onBack={goToList} />;
  return <CardListScreen onViewCard={goToDetail} onEditCard={goToEdit} />;
}
