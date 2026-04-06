'use client';

/**
 * AuthorizationDetailCard — full detail view of a single authorization.
 *
 * Maps COPAU01 (COPAU1A map) fields to a modern card layout.
 * All fields are read-only (ASKIP on original screen).
 * AUTHMTCO (match_status) and AUTHFRDO (fraud_status) shown with red emphasis.
 * CARDNUM, AUTHDT, AUTHTM, AUTHRSP shown in pink/magenta (identity fields row 7).
 *
 * Does not include fraud toggle button — caller provides that.
 */

import type { AuthDetailResponse } from '@/types/authorization';
import { MATCH_STATUS_LABELS } from '@/types/authorization';
import { formatAuthDate, formatAuthTime, formatCurrency, getApprovalConfig } from '@/lib/utils';
import { MerchantInfoCard } from './MerchantInfoCard';

interface AuthorizationDetailCardProps {
  detail: AuthDetailResponse;
}

interface FieldProps {
  label: string;
  value: React.ReactNode;
  valueClassName?: string;
  labelClassName?: string;
}

function Field({ label, value, valueClassName = '', labelClassName = '' }: FieldProps) {
  return (
    <div>
      <label
        className={`block text-xs font-medium text-cyan-600 uppercase tracking-wider mb-1 ${labelClassName}`}
      >
        {label}
      </label>
      <div className={`text-sm font-medium ${valueClassName || 'text-blue-700'}`}>
        {value ?? '—'}
      </div>
    </div>
  );
}

export function AuthorizationDetailCard({ detail }: AuthorizationDetailCardProps) {
  const approvalConfig = getApprovalConfig(detail.approval_status);

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="p-6">
        {/* Row 7: Identity fields — Card #, Auth Date, Auth Time (PINK in COPAU01) */}
        <div className="grid grid-cols-3 gap-6 mb-6 pb-6 border-b border-gray-100">
          <Field
            label="Card #"
            value={detail.card_number_masked}
            valueClassName="text-pink-700 font-mono font-semibold"
          />
          <Field
            label="Auth Date"
            value={formatAuthDate(detail.auth_date)}
            valueClassName="text-pink-700"
          />
          <Field
            label="Auth Time"
            value={formatAuthTime(detail.auth_time)}
            valueClassName="text-pink-700"
          />
        </div>

        {/* Row 9: Response fields — Auth Resp, Reason, Auth Code */}
        <div className="grid grid-cols-3 gap-6 mb-6 pb-6 border-b border-gray-100">
          <Field
            label="Auth Response"
            value={
              <span className={approvalConfig.className}>
                {detail.auth_response_code} — {approvalConfig.label}
              </span>
            }
          />
          <Field
            label="Response Reason"
            value={detail.decline_reason}
          />
          <Field
            label="Auth Code"
            value={detail.auth_code}
          />
        </div>

        {/* Row 11: Transaction fields — Amount, POS Entry Mode, Source */}
        <div className="grid grid-cols-3 gap-6 mb-6 pb-6 border-b border-gray-100">
          <Field
            label="Amount"
            value={formatCurrency(detail.amount)}
          />
          <Field
            label="POS Entry Mode"
            value={detail.pos_entry_mode}
          />
          <Field
            label="Source"
            value={detail.auth_source}
          />
        </div>

        {/* Row 13: Classification fields — MCC Code, Card Exp, Auth Type */}
        <div className="grid grid-cols-3 gap-6 mb-6 pb-6 border-b border-gray-100">
          <Field
            label="MCC Code"
            value={detail.mcc_code}
          />
          <Field
            label="Card Exp. Date"
            value={detail.card_expiry}
          />
          <Field
            label="Auth Type"
            value={detail.auth_type}
          />
        </div>

        {/* Row 15: Status fields — Tran ID, Match Status (RED), Fraud Status (RED) */}
        <div className="grid grid-cols-3 gap-6 mb-2">
          <Field
            label="Transaction ID"
            value={
              <span className="font-mono text-sm">{detail.transaction_id}</span>
            }
          />
          <Field
            label="Match Status"
            value={
              <span className="font-semibold text-red-700">
                {detail.match_status} — {MATCH_STATUS_LABELS[detail.match_status] ?? detail.match_status}
              </span>
            }
            valueClassName="text-red-700"
          />
          <Field
            label="Fraud Status"
            value={
              <span className={`font-semibold ${detail.fraud_status !== 'N' ? 'text-red-700' : 'text-green-700'}`}>
                {detail.fraud_status_display || 'No Fraud'}
              </span>
            }
          />
        </div>

        {/* Row 17-21: Merchant Details section with separator */}
        <MerchantInfoCard
          merchantName={detail.merchant_name}
          merchantId={detail.merchant_id}
          merchantCity={detail.merchant_city}
          merchantState={detail.merchant_state}
          merchantZip={detail.merchant_zip}
        />
      </div>
    </div>
  );
}
