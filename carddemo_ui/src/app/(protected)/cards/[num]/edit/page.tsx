"use client";

import { useParams } from "next/navigation";
import CardForm from "@/components/cards/CardForm";

export default function CardEditPage() {
  const params = useParams();
  const cardNum = params.num as string;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Edit Card</h2>
      <CardForm cardNum={cardNum} />
    </div>
  );
}
