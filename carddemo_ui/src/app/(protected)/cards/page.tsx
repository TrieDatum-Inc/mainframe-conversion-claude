"use client";

import Link from "next/link";
import CardTable from "@/components/cards/CardTable";

export default function CardsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Credit Cards</h2>
      </div>
      <CardTable />
    </div>
  );
}
