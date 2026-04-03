/**
 * Home / Landing page — presents choice between View and Update.
 * Equivalent to COMEN01C main menu options for account management.
 */

import Link from "next/link";
import { ScreenHeader } from "@/components/ui/ScreenHeader";

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      <ScreenHeader
        tranId="CM00"
        progName="COMEN01C"
        title01="AWS CardDemo"
        title02="Account Management"
      />
      <main className="flex-1 flex flex-col items-center justify-center gap-8 p-8">
        <h1 className="text-2xl font-bold text-gray-800">
          CardDemo — Account Management
        </h1>
        <p className="text-gray-500 text-sm">
          Converted from IBM COBOL/CICS — COACTVWC &amp; COACTUPC
        </p>
        <div className="flex gap-6">
          <Link
            href="/accounts"
            className="flex flex-col items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-8 py-6 text-center hover:bg-blue-100 transition-colors"
          >
            <span className="text-3xl">&#128269;</span>
            <span className="font-semibold text-blue-800">View Account</span>
            <span className="text-xs text-gray-500">COACTVWC / CAVW</span>
          </Link>
          <Link
            href="/accounts/update"
            className="flex flex-col items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-8 py-6 text-center hover:bg-green-100 transition-colors"
          >
            <span className="text-3xl">&#9998;</span>
            <span className="font-semibold text-green-800">Update Account</span>
            <span className="text-xs text-gray-500">COACTUPC / CAUP</span>
          </Link>
        </div>
      </main>
    </div>
  );
}
