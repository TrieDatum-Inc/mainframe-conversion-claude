"use client";

/**
 * AccountDetail — full account + customer detail view.
 *
 * Modernizes COACTVWC screen layout:
 *   - Account financial data section (balance, limits, dates, group)
 *   - Customer demographics section (name, address, phone, SSN, FICO)
 *   - Associated cards section (CARDAIX browse result)
 *
 * Edit button navigates to /accounts/[id]/edit (COACTUPC transition).
 */

import { useRouter } from "next/navigation";
import type { AccountDetail as AccountDetailType } from "@/types";

interface AccountDetailProps {
  account: AccountDetailType;
}

function formatCurrency(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  return isNaN(num)
    ? String(value)
    : num.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

function formatDate(value: string | null): string {
  if (!value) return "--";
  return new Date(value).toLocaleDateString("en-US");
}

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-200 px-6 py-4">
        <h2 className="text-base font-semibold text-gray-900">{title}</h2>
      </div>
      <div className="px-6 py-4">{children}</div>
    </div>
  );
}

function FieldRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="grid grid-cols-2 gap-4 py-2 border-b border-gray-50 last:border-b-0">
      <dt className="text-sm font-medium text-gray-500">{label}</dt>
      <dd className="text-sm text-gray-900">{value ?? "--"}</dd>
    </div>
  );
}

export function AccountDetail({ account }: AccountDetailProps) {
  const router = useRouter();
  const customer = account.customer;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Account {account.account_id}
          </h1>
          <span
            className={`mt-1 inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
              account.active_status === "Y"
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            {account.active_status === "Y" ? "Active" : "Inactive"}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => router.push("/accounts")}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Back to List
          </button>
          <button
            onClick={() => router.push(`/accounts/${account.account_id}/edit`)}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Edit Account
          </button>
        </div>
      </div>

      {/* Account Financial Info */}
      <SectionCard title="Account Financial Information">
        <dl>
          <FieldRow label="Current Balance" value={formatCurrency(account.current_balance)} />
          <FieldRow label="Credit Limit" value={formatCurrency(account.credit_limit)} />
          <FieldRow label="Cash Credit Limit" value={formatCurrency(account.cash_credit_limit)} />
          <FieldRow label="Current Cycle Credits" value={formatCurrency(account.current_cycle_credit)} />
          <FieldRow label="Current Cycle Debits" value={formatCurrency(account.current_cycle_debit)} />
          <FieldRow label="Open Date" value={formatDate(account.open_date)} />
          <FieldRow label="Expiration Date" value={formatDate(account.expiration_date)} />
          <FieldRow label="Reissue Date" value={formatDate(account.reissue_date)} />
          <FieldRow label="Group ID" value={account.group_id} />
          <FieldRow label="Address Zip" value={account.address_zip} />
        </dl>
      </SectionCard>

      {/* Customer Info */}
      {customer ? (
        <SectionCard title="Customer Information">
          <dl>
            <FieldRow label="Customer ID" value={customer.customer_id} />
            <FieldRow
              label="Name"
              value={[customer.first_name, customer.middle_name, customer.last_name]
                .filter(Boolean)
                .join(" ")}
            />
            <FieldRow label="Address" value={
              <div>
                {customer.address_line_1 && <div>{customer.address_line_1}</div>}
                {customer.address_line_2 && <div>{customer.address_line_2}</div>}
                {customer.address_line_3 && <div>{customer.address_line_3}</div>}
                <div>
                  {[customer.state_code, customer.zip_code, customer.country_code]
                    .filter(Boolean)
                    .join(" ")}
                </div>
              </div>
            } />
            <FieldRow label="Phone 1" value={customer.phone_1} />
            <FieldRow label="Phone 2" value={customer.phone_2} />
            <FieldRow label="SSN" value={customer.ssn || "--"} />
            <FieldRow label="Date of Birth" value={formatDate(customer.date_of_birth)} />
            <FieldRow label="FICO Score" value={customer.fico_score?.toString()} />
            <FieldRow label="Government ID" value={customer.govt_issued_id} />
            <FieldRow label="EFT Account" value={customer.eft_account_id} />
            <FieldRow
              label="Primary Card Holder"
              value={customer.primary_card_holder === "Y" ? "Yes" : "No"}
            />
          </dl>
        </SectionCard>
      ) : (
        <SectionCard title="Customer Information">
          <p className="text-sm text-gray-500">No customer linked to this account.</p>
        </SectionCard>
      )}

      {/* Associated Cards */}
      <SectionCard title={`Associated Cards (${account.cards.length})`}>
        {account.cards.length === 0 ? (
          <p className="text-sm text-gray-500">No cards linked to this account.</p>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Card Number
                </th>
                <th className="py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Name on Card
                </th>
                <th className="py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Status
                </th>
                <th className="py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Expiry
                </th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {account.cards.map((card) => (
                <tr key={card.card_number} className="hover:bg-gray-50">
                  <td className="py-3 text-sm font-mono text-gray-900">{card.card_number}</td>
                  <td className="py-3 text-sm text-gray-700">{card.embossed_name}</td>
                  <td className="py-3 text-sm">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        card.active_status === "Y"
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {card.active_status === "Y" ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="py-3 text-sm text-gray-500">
                    {formatDate(card.expiration_date)}
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => router.push(`/cards/${card.card_number}`)}
                      className="text-xs text-brand-600 hover:underline"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </SectionCard>
    </div>
  );
}
