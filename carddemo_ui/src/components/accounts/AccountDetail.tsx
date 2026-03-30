"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AccountView } from "@/lib/types";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AlertMessage from "@/components/ui/AlertMessage";
import StatusBadge from "@/components/ui/StatusBadge";

interface AccountDetailProps {
  acctId: string;
}

export default function AccountDetail({ acctId }: AccountDetailProps) {
  const [account, setAccount] = useState<AccountView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!acctId) return;
    setLoading(true);
    setError("");
    api
      .get<AccountView>(`/api/accounts/${acctId}`)
      .then(setAccount)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [acctId]);

  if (loading) return <LoadingSpinner />;
  if (error) return <AlertMessage type="error" message={error} />;
  if (!account) return <AlertMessage type="info" message="No account data found." />;

  const currency = (val: number) =>
    new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(val);

  return (
    <div className="space-y-6">
      {/* Account Information */}
      <section className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
          <h3 className="text-sm font-semibold text-gray-700">Account Information</h3>
        </div>
        <dl className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt className="text-xs font-medium text-gray-500">Account ID</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-900">{account.acct_id}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Status</dt>
            <dd className="mt-1">
              <StatusBadge status={account.acct_active_status === "Y" ? "Active" : "Inactive"} />
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Group ID</dt>
            <dd className="mt-1 text-sm text-gray-900">{account.acct_group_id}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Current Balance</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-900">{currency(account.acct_curr_bal)}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Credit Limit</dt>
            <dd className="mt-1 text-sm text-gray-900">{currency(account.acct_credit_limit)}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Cash Credit Limit</dt>
            <dd className="mt-1 text-sm text-gray-900">{currency(account.acct_cash_credit_limit)}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Current Cycle Credit</dt>
            <dd className="mt-1 text-sm text-gray-900">{currency(account.acct_curr_cyc_credit)}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Current Cycle Debit</dt>
            <dd className="mt-1 text-sm text-gray-900">{currency(account.acct_curr_cyc_debit)}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Open Date</dt>
            <dd className="mt-1 text-sm text-gray-900">{account.acct_open_date}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Expiration Date</dt>
            <dd className="mt-1 text-sm text-gray-900">{account.acct_expiration_date}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Reissue Date</dt>
            <dd className="mt-1 text-sm text-gray-900">{account.acct_reissue_date}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">ZIP Code</dt>
            <dd className="mt-1 text-sm text-gray-900">{account.acct_addr_zip}</dd>
          </div>
        </dl>
      </section>

      {/* Customer Information */}
      {account.cust_id && (
        <section className="rounded-lg border border-gray-200 bg-white">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
            <h3 className="text-sm font-semibold text-gray-700">Customer Information</h3>
          </div>
          <dl className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <dt className="text-xs font-medium text-gray-500">Customer ID</dt>
              <dd className="mt-1 text-sm text-gray-900">{account.cust_id}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">Name</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {[account.cust_first_name, account.cust_middle_name, account.cust_last_name]
                  .filter(Boolean)
                  .join(" ")}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">Date of Birth</dt>
              <dd className="mt-1 text-sm text-gray-900">{account.cust_dob_yyyymmdd ?? "—"}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-xs font-medium text-gray-500">Address</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {[
                  account.cust_addr_line_1,
                  account.cust_addr_line_2,
                  account.cust_addr_line_3,
                ].filter(Boolean).join(", ")}
                {account.cust_addr_state_cd && `, ${account.cust_addr_state_cd}`}
                {account.cust_addr_zip && ` ${account.cust_addr_zip}`}
                {account.cust_addr_country_cd && `, ${account.cust_addr_country_cd}`}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">Phone 1</dt>
              <dd className="mt-1 text-sm text-gray-900">{account.cust_phone_num_1 ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">Phone 2</dt>
              <dd className="mt-1 text-sm text-gray-900">{account.cust_phone_num_2 ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">SSN</dt>
              <dd className="mt-1 text-sm text-gray-900">{account.cust_ssn ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">Govt. Issued ID</dt>
              <dd className="mt-1 text-sm text-gray-900">{account.cust_govt_issued_id ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">EFT Account</dt>
              <dd className="mt-1 text-sm text-gray-900">{account.cust_eft_account_id ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">Primary Card Holder</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {account.cust_pri_card_holder_ind === "Y" ? "Yes" : "No"}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-gray-500">FICO Score</dt>
              <dd className="mt-1 text-sm text-gray-900">{account.cust_fico_credit_score ?? "—"}</dd>
            </div>
          </dl>
        </section>
      )}
    </div>
  );
}
