"use client";

/**
 * AuthDetail Component
 *
 * Renders full authorization detail matching COPAU01 BMS screen layout:
 *   Row 7:  Card Number, Auth Date, Time
 *   Row 9:  Response (A/D colored), Reason, Auth Code
 *   Row 11: Amount, POS Mode, Source
 *   Row 13: MCC Code, Card Expiry, Auth Type
 *   Row 15: Transaction ID, Match Status (highlighted), Fraud Status (RED if F)
 *   Row 17: Merchant Details section header
 *   Row 19: Merchant Name, ID
 *   Row 21: Merchant City, State, Zip
 *
 * F5 (Mark/Remove Fraud) → FraudToggle component
 * F8 (Next Auth) → navigates to next/previous records
 */

import { useRouter } from "next/navigation";
import type { AuthorizationDetail } from "@/types";
import { FraudToggle } from "./FraudToggle";
import {
  formatCurrency,
  formatDate,
  formatTime,
  getFraudBadgeClasses,
  getMatchStatusClasses,
  getResponseBadgeClasses,
  maskCardNumber,
} from "@/lib/utils";
import { DECLINE_REASON_CODES } from "@/types";

interface AuthDetailProps {
  accountId: string;
  detail: AuthorizationDetail;
  onFraudToggled?: () => void;
}

function DetailRow({ label, value, className = "" }: {
  label: string;
  value: React.ReactNode;
  className?: string;
}) {
  return (
    <div className="flex justify-between items-start py-1.5 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-500 min-w-[140px]">{label}</span>
      <span className={`text-sm text-right ${className}`}>{value}</span>
    </div>
  );
}

export function AuthDetail({ accountId, detail, onFraudToggled }: AuthDetailProps) {
  const router = useRouter();
  const isApproved = detail.auth_response_code === "00";

  const handleBack = () => {
    router.push(`/authorizations/${accountId}`);
  };

  return (
    <div className="space-y-4">
      {/* Back navigation */}
      <button
        onClick={handleBack}
        className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 transition-colors"
      >
        &larr; F3 Back to Authorization List
      </button>

      <h1 className="text-xl font-semibold text-gray-900">View Authorization Details</h1>

      {/* Card Info (BMS Row 7) */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
          Card Information
        </h2>
        <DetailRow label="Card Number" value={
          <span className="font-mono text-pink-700 font-medium">
            {maskCardNumber(detail.card_number)}
          </span>
        } />
        <DetailRow label="Auth Date" value={formatDate(detail.auth_date)} />
        <DetailRow label="Auth Time" value={formatTime(detail.auth_time)} />
        <DetailRow label="Card Expiry" value={detail.card_expiry} />
        <DetailRow label="Auth Type" value={detail.auth_type} />
      </div>

      {/* Response Info (BMS Row 9) */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
          Authorization Response
        </h2>
        <DetailRow
          label="Response"
          value={
            <span
              className={`px-3 py-0.5 rounded text-xs font-bold ${getResponseBadgeClasses(
                isApproved ? "A" : "D"
              )}`}
            >
              {isApproved ? "APPROVED" : "DECLINED"}
            </span>
          }
        />
        <DetailRow
          label="Reason Code"
          value={`${detail.auth_response_code} — ${
            DECLINE_REASON_CODES[detail.auth_response_code] ?? "UNKNOWN"
          }`}
        />
        <DetailRow
          label="Response Reason"
          value={detail.decline_reason_description ?? detail.auth_response_reason}
        />
        <DetailRow label="Auth Code" value={
          <span className="font-mono">{detail.auth_code || "—"}</span>
        } />
      </div>

      {/* Financial Info (BMS Row 11) */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
          Financial Details
        </h2>
        <DetailRow
          label="Transaction Amount"
          value={
            <span className="font-semibold">
              {formatCurrency(detail.transaction_amount)}
            </span>
          }
        />
        <DetailRow
          label="Approved Amount"
          value={
            <span className={isApproved ? "text-green-700 font-semibold" : "text-gray-400"}>
              {formatCurrency(detail.approved_amount)}
            </span>
          }
        />
        <DetailRow label="POS Entry Mode" value={detail.pos_entry_mode || "—"} />
        <DetailRow label="Auth Source" value={detail.auth_source || "—"} />
        <DetailRow label="Processing Code" value={
          <span className="font-mono">{detail.processing_code || "—"}</span>
        } />
      </div>

      {/* Classification (BMS Row 13) */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
          Classification
        </h2>
        <DetailRow label="MCC Code" value={detail.mcc_code || "—"} />
        <DetailRow label="Message Type" value={detail.message_type || "—"} />
      </div>

      {/* Tracking (BMS Row 15) — fraud status highlighted RED */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
          Tracking
        </h2>
        <DetailRow
          label="Transaction ID"
          value={<span className="font-mono text-xs">{detail.transaction_id}</span>}
        />
        <DetailRow
          label="Match Status"
          value={
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium ${getMatchStatusClasses(
                detail.match_status
              )}`}
            >
              {detail.match_status}
            </span>
          }
        />
        <DetailRow
          label="Fraud Status"
          value={
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium ${getFraudBadgeClasses(
                detail.fraud_status
              )}`}
            >
              {detail.fraud_status === "F"
                ? "FRAUD CONFIRMED"
                : detail.fraud_status === "R"
                  ? "FRAUD REMOVED"
                  : "None"}
            </span>
          }
        />
        {detail.fraud_report_date && (
          <DetailRow
            label="Fraud Report Date"
            value={formatDate(detail.fraud_report_date)}
          />
        )}
      </div>

      {/* Merchant Details (BMS Rows 17-21) */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
          Merchant Details ─────────────────────
        </h2>
        <DetailRow label="Merchant Name" value={detail.merchant_name || "—"} />
        <DetailRow label="Merchant ID" value={
          <span className="font-mono text-xs">{detail.merchant_id || "—"}</span>
        } />
        <DetailRow label="City" value={detail.merchant_city || "—"} />
        <DetailRow label="State" value={detail.merchant_state || "—"} />
        <DetailRow label="ZIP Code" value={detail.merchant_zip || "—"} />
      </div>

      {/* Action Buttons (F5=Fraud, F8=Next) */}
      <div className="flex items-center gap-3 pt-2">
        <FraudToggle
          detailId={detail.id}
          currentFraudStatus={detail.fraud_status}
          onSuccess={onFraudToggled}
        />
        <button
          onClick={handleBack}
          className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          F3 Back
        </button>
      </div>
    </div>
  );
}
