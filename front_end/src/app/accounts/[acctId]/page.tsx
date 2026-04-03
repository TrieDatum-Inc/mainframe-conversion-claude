/**
 * Account View detail page — COACTVWC / CACTVWA screen.
 *
 * Displays the full account + customer + cards read-only view.
 * Corresponds to COACTVWC after 9000-READ-ACCT + 1200-SETUP-SCREEN-VARS.
 *
 * Screen layout mirrors CACTVWA BMS map field positions:
 * - Row 4:  "View Account" section header
 * - Row 5:  Account number + Active Y/N
 * - Rows 6-10: Account financial data
 * - Row 11: "Customer Details" section header
 * - Rows 12-20: Customer info
 * - Row 24: F3=Exit navigation
 */

import { notFound } from "next/navigation";
import Link from "next/link";
import { getAccount } from "@/lib/api";
import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { ReadOnlyField } from "@/components/ui/ReadOnlyField";
import { AccountSearchForm } from "@/components/forms/AccountSearchForm";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { AccountDetailResponse } from "@/types/account";

interface Props {
  params: { acctId: string };
}

export default async function AccountViewPage({ params }: Props) {
  const { acctId } = params;

  let account: AccountDetailResponse;
  let errorMsg: string | null = null;

  try {
    account = await getAccount(acctId);
  } catch (err: unknown) {
    const isAxios =
      err &&
      typeof err === "object" &&
      "response" in err &&
      (err as { response?: { status?: number } }).response?.status === 404;
    if (isAxios) {
      return notFound();
    }
    errorMsg = err instanceof Error ? err.message : "Error loading account";

    return (
      <div className="min-h-screen flex flex-col">
        <ScreenHeader tranId="CAVW" progName="COACTVWC" title01="AWS CardDemo" title02="Account View" />
        <main className="flex-1 p-6">
          <SectionHeader title="View Account" />
          <div className="mt-4 max-w-lg">
            <AccountSearchForm mode="view" defaultAcctId={acctId} />
          </div>
          <div className="mt-4 rounded border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-700" role="alert">
            {errorMsg}
          </div>
        </main>
      </div>
    );
  }

  const c = account.customer;

  return (
    <div className="min-h-screen flex flex-col">
      <ScreenHeader
        tranId="CAVW"
        progName="COACTVWC"
        title01="AWS CardDemo"
        title02="Account View"
      />

      <main className="flex-1 p-4 max-w-4xl mx-auto w-full">
        {/* Row 4: Section header */}
        <SectionHeader title="View Account" />

        {/* Search form — always visible for ACCTSID re-entry */}
        <div className="mt-3 mb-4">
          <AccountSearchForm mode="view" defaultAcctId={acctId} />
        </div>

        {/* ---- Account section (rows 5-10 of CACTVWA) ---- */}
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 border-t pt-3">
          {/* Row 5 */}
          <div className="flex items-center gap-6">
            <ReadOnlyField label="Account Number" value={account.acct_id} className="flex-1" />
            <ReadOnlyField
              label="Active Y/N"
              value={account.acct_active_status}
              className="w-16"
              valueClassName={account.acct_active_status === "Y" ? "text-green-700" : "text-red-700"}
            />
          </div>

          {/* Row 6 */}
          <div className="flex items-center gap-6">
            <ReadOnlyField label="Opened" value={formatDate(account.acct_open_date)} className="flex-1" />
            <ReadOnlyField
              label="Credit Limit"
              value={formatCurrency(Number(account.acct_credit_limit))}
              className="flex-1"
              valueClassName="font-mono text-right"
            />
          </div>

          {/* Row 7 */}
          <div className="flex items-center gap-6">
            <ReadOnlyField label="Expiry" value={formatDate(account.acct_expiration_date)} className="flex-1" />
            <ReadOnlyField
              label="Cash Credit Limit"
              value={formatCurrency(Number(account.acct_cash_credit_limit))}
              className="flex-1"
              valueClassName="font-mono text-right"
            />
          </div>

          {/* Row 8 */}
          <div className="flex items-center gap-6">
            <ReadOnlyField label="Reissue" value={formatDate(account.acct_reissue_date)} className="flex-1" />
            <ReadOnlyField
              label="Current Balance"
              value={formatCurrency(Number(account.acct_curr_bal))}
              className="flex-1"
              valueClassName="font-mono text-right"
            />
          </div>

          {/* Row 9 */}
          <div className="col-start-2">
            <ReadOnlyField
              label="Current Cycle Credit"
              value={formatCurrency(Number(account.acct_curr_cyc_credit))}
              valueClassName="font-mono text-right"
            />
          </div>

          {/* Row 10 */}
          <div className="flex items-center gap-6">
            <ReadOnlyField label="Account Group" value={account.acct_group_id} className="flex-1" />
            <ReadOnlyField
              label="Current Cycle Debit"
              value={formatCurrency(Number(account.acct_curr_cyc_debit))}
              className="flex-1"
              valueClassName="font-mono text-right"
            />
          </div>
        </div>

        {/* ---- Customer section (rows 11-20 of CACTVWA) ---- */}
        <div className="mt-4 border-t pt-2">
          <SectionHeader title="Customer Details" className="text-sm" />

          {!c ? (
            <p className="text-sm text-gray-500 mt-2">
              Did not find associated customer in master file
            </p>
          ) : (
            <div className="grid grid-cols-3 gap-x-6 gap-y-2 mt-2">
              {/* Row 12 */}
              <ReadOnlyField label="Customer ID" value={c.cust_id} />
              <ReadOnlyField label="SSN" value={c.ssn_formatted} />
              <div />

              {/* Row 13 */}
              <ReadOnlyField label="Date of Birth" value={formatDate(c.cust_dob)} />
              <ReadOnlyField label="FICO Score" value={c.cust_fico_credit_score} />
              <div />

              {/* Row 14/15: Names */}
              <ReadOnlyField label="First Name" value={c.cust_first_name} />
              <ReadOnlyField label="Middle Name" value={c.cust_middle_name} />
              <ReadOnlyField label="Last Name" value={c.cust_last_name} />

              {/* Row 16: Address */}
              <div className="col-span-2">
                <ReadOnlyField label="Address" value={c.cust_addr_line_1} />
              </div>
              <ReadOnlyField label="State" value={c.cust_addr_state_cd} />

              <div className="col-span-2">
                <ReadOnlyField label="" value={c.cust_addr_line_2} />
              </div>
              <ReadOnlyField label="ZIP" value={c.cust_addr_zip} />

              {/* Row 18 */}
              <div className="col-span-2">
                <ReadOnlyField label="City" value={c.cust_addr_line_3} />
              </div>
              <ReadOnlyField label="Country" value={c.cust_addr_country_cd} />

              {/* Row 19 */}
              <ReadOnlyField label="Phone 1" value={c.cust_phone_num_1} />
              <div className="col-span-2">
                <ReadOnlyField label="Government Issued ID" value={c.cust_govt_issued_id} />
              </div>

              {/* Row 20 */}
              <ReadOnlyField label="Phone 2" value={c.cust_phone_num_2} />
              <ReadOnlyField label="EFT Account ID" value={c.cust_eft_account_id} />
              <ReadOnlyField label="Primary Card Holder Y/N" value={c.cust_pri_card_holder_ind} />
            </div>
          )}
        </div>

        {/* ---- Cards section ---- */}
        {account.cards.length > 0 && (
          <div className="mt-4 border-t pt-2">
            <h3 className="text-sm font-semibold text-gray-600 mb-2">
              Linked Cards ({account.cards.length})
            </h3>
            <div className="grid grid-cols-4 gap-2 text-xs">
              <span className="font-semibold text-cyan-700">Card Number</span>
              <span className="font-semibold text-cyan-700">Embossed Name</span>
              <span className="font-semibold text-cyan-700">Expiry</span>
              <span className="font-semibold text-cyan-700">Status</span>
              {account.cards.map((card) => (
                <>
                  <span key={`n-${card.card_num}`} className="font-mono">{card.card_num}</span>
                  <span key={`e-${card.card_num}`}>{card.card_embossed_name}</span>
                  <span key={`x-${card.card_num}`}>{formatDate(card.card_expiration_date)}</span>
                  <span
                    key={`s-${card.card_num}`}
                    className={card.card_active_status === "Y" ? "text-green-700" : "text-red-600"}
                  >
                    {card.card_active_status === "Y" ? "Active" : "Inactive"}
                  </span>
                </>
              ))}
            </div>
          </div>
        )}

        {/* Row 24: Navigation bar — mirrors BMS literal 'F3=Exit' */}
        <div className="mt-6 border-t pt-3 flex items-center gap-4 text-sm">
          <Link href="/accounts" className="text-cyan-700 hover:underline font-medium">
            F3=Exit
          </Link>
          <Link
            href={`/accounts/${acctId}/update`}
            className="ml-4 text-blue-700 hover:underline font-medium"
          >
            Update this Account
          </Link>
        </div>
      </main>
    </div>
  );
}
