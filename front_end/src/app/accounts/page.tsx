/**
 * Account View search page.
 * First state of COACTVWC: blank screen with ACCTSID input.
 * Maps to: COACTVWC CDEMO-PGM-ENTER → 1000-SEND-MAP (blank screen).
 */

import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { AccountSearchForm } from "@/components/forms/AccountSearchForm";
import { SectionHeader } from "@/components/ui/SectionHeader";

export default function AccountSearchPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <ScreenHeader
        tranId="CAVW"
        progName="COACTVWC"
        title01="AWS CardDemo"
        title02="Account View"
      />
      <main className="flex-1 p-6">
        <SectionHeader title="View Account" />
        <div className="mt-6 max-w-lg mx-auto">
          <p className="mb-4 text-sm text-gray-500">
            Enter or update id of account to display
          </p>
          <AccountSearchForm mode="view" />
        </div>
      </main>
    </div>
  );
}
