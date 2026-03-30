"use client";

import { useParams } from "next/navigation";
import CardDetailComponent from "@/components/cards/CardDetail";

export default function CardDetailPage() {
  const params = useParams();
  const cardNum = params.num as string;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Card Details</h2>
      <CardDetailComponent cardNum={cardNum} />
    </div>
  );
}
