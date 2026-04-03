/**
 * Account Update search page — COACTUPC blank/initial state.
 * Equivalent to COACTUPC ACUP-DETAILS-NOT-FETCHED → blank screen.
 */

import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { AccountSearchForm } from "@/components/forms/AccountSearchForm";
import { SectionHeader } from "@/components/ui/SectionHeader";

export default function AccountUpdateSearchPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <ScreenHeader
        tranId="CAUP"
        progName="COACTUPC"
        title01="AWS CardDemo"
        title02="Account Update"
      />
      <main className="flex-1 p-6">
        <SectionHeader title="Update Account" />
        <div className="mt-6 max-w-lg mx-auto">
          <p className="mb-4 text-sm text-gray-500">
            Enter or update id of account to update
          </p>
          <AccountSearchForm mode="update" />
        </div>
      </main>
    </div>
  );
}
