"use client";

/**
 * AuthProcessForm Component
 *
 * Form to submit a new authorization request.
 * Replaces the IMS+MQ COPAUA0C processing flow.
 * Shows result: Approved (green) / Declined (red) with reason code.
 */

import { useState } from "react";
import { processAuthorization } from "@/lib/api";
import type { AuthorizationProcessRequest, AuthorizationProcessResponse } from "@/types";
import { DECLINE_REASON_CODES } from "@/types";
import { formatCurrency } from "@/lib/utils";

const INITIAL_FORM: AuthorizationProcessRequest = {
  card_number: "",
  card_expiry: "",
  amount: "",
  auth_type: "SALE",
  message_type: "0110",
  pos_entry_mode: "0101",
  processing_code: "000000",
  mcc_code: "",
  merchant_name: "",
  merchant_id: "",
  merchant_city: "",
  merchant_state: "",
  merchant_zip: "",
};

function FormField({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {children}
    </div>
  );
}

const inputClass =
  "w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent";

export function AuthProcessForm() {
  const [form, setForm] = useState<AuthorizationProcessRequest>(INITIAL_FORM);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AuthorizationProcessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (field: keyof AuthorizationProcessRequest, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await processAuthorization(form);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authorization request failed");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setForm(INITIAL_FORM);
    setResult(null);
    setError(null);
  };

  const isApproved = result?.auth_response === "A";

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-semibold text-gray-900 mb-1">
        Process Authorization
      </h1>
      <p className="text-sm text-gray-500 mb-6">
        Submit a card authorization request. Replaces the COPAUA0C IMS+MQ processing engine.
      </p>

      {/* Result Banner */}
      {result && (
        <div
          className={`mb-6 p-5 rounded-lg border-2 ${
            isApproved
              ? "bg-green-50 border-green-300"
              : "bg-red-50 border-red-300"
          }`}
        >
          <div className="flex items-center gap-3 mb-3">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                isApproved ? "bg-green-500" : "bg-red-500"
              }`}
            >
              {isApproved ? "A" : "D"}
            </div>
            <div>
              <p className={`font-bold text-lg ${isApproved ? "text-green-800" : "text-red-800"}`}>
                {isApproved ? "APPROVED" : "DECLINED"}
              </p>
              <p className="text-xs text-gray-500">
                Code: {result.auth_response_code} &mdash;{" "}
                {DECLINE_REASON_CODES[result.auth_response_code] ?? "UNKNOWN"}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500">Transaction ID</span>
              <p className="font-mono font-medium">{result.transaction_id}</p>
            </div>
            {isApproved && (
              <div>
                <span className="text-gray-500">Auth Code</span>
                <p className="font-mono font-medium">{result.auth_code}</p>
              </div>
            )}
            <div>
              <span className="text-gray-500">Requested Amount</span>
              <p className="font-medium">{formatCurrency(result.transaction_amount)}</p>
            </div>
            <div>
              <span className="text-gray-500">Approved Amount</span>
              <p className={`font-medium ${isApproved ? "text-green-700" : "text-gray-400"}`}>
                {formatCurrency(result.approved_amount)}
              </p>
            </div>
            {!isApproved && result.decline_reason && (
              <div className="col-span-2">
                <span className="text-gray-500">Decline Reason</span>
                <p className="font-medium text-red-700">{result.decline_reason}</p>
              </div>
            )}
          </div>
          <button
            onClick={handleReset}
            className="mt-4 px-4 py-1.5 text-sm border border-gray-300 rounded-md text-gray-600 hover:bg-white transition-colors"
          >
            New Request
          </button>
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      )}

      {!result && (
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Card Information */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">
              Card Information
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <FormField label="Card Number" required>
                  <input
                    type="text"
                    value={form.card_number}
                    onChange={(e) => handleChange("card_number", e.target.value)}
                    placeholder="4111111111111111"
                    maxLength={16}
                    pattern="\d{13,16}"
                    required
                    className={inputClass}
                  />
                </FormField>
              </div>
              <FormField label="Card Expiry (MM/YY)" required>
                <input
                  type="text"
                  value={form.card_expiry}
                  onChange={(e) => handleChange("card_expiry", e.target.value)}
                  placeholder="12/28"
                  pattern="\d{2}/\d{2}"
                  required
                  className={inputClass}
                />
              </FormField>
              <FormField label="Amount (USD)" required>
                <input
                  type="number"
                  value={form.amount}
                  onChange={(e) => handleChange("amount", e.target.value)}
                  placeholder="100.00"
                  min="0.01"
                  step="0.01"
                  required
                  className={inputClass}
                />
              </FormField>
            </div>
          </div>

          {/* Transaction Details */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">
              Transaction Details
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <FormField label="Auth Type">
                <select
                  value={form.auth_type}
                  onChange={(e) => handleChange("auth_type", e.target.value)}
                  className={inputClass}
                >
                  <option value="SALE">SALE</option>
                  <option value="AUTH">AUTH</option>
                  <option value="VOID">VOID</option>
                  <option value="REFD">REFD</option>
                </select>
              </FormField>
              <FormField label="MCC Code">
                <input
                  type="text"
                  value={form.mcc_code}
                  onChange={(e) => handleChange("mcc_code", e.target.value)}
                  placeholder="5411"
                  maxLength={4}
                  className={inputClass}
                />
              </FormField>
              <FormField label="POS Entry Mode">
                <select
                  value={form.pos_entry_mode}
                  onChange={(e) => handleChange("pos_entry_mode", e.target.value)}
                  className={inputClass}
                >
                  <option value="0101">0101 — Manual/Keyed</option>
                  <option value="0201">0201 — Chip</option>
                  <option value="0901">0901 — Contactless</option>
                </select>
              </FormField>
            </div>
          </div>

          {/* Merchant Details */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">
              Merchant Details
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <FormField label="Merchant Name">
                  <input
                    type="text"
                    value={form.merchant_name}
                    onChange={(e) => handleChange("merchant_name", e.target.value)}
                    placeholder="WHOLE FOODS MARKET"
                    maxLength={25}
                    className={inputClass}
                  />
                </FormField>
              </div>
              <FormField label="Merchant ID">
                <input
                  type="text"
                  value={form.merchant_id}
                  onChange={(e) => handleChange("merchant_id", e.target.value)}
                  placeholder="MERCH0000001"
                  maxLength={15}
                  className={inputClass}
                />
              </FormField>
              <FormField label="City">
                <input
                  type="text"
                  value={form.merchant_city}
                  onChange={(e) => handleChange("merchant_city", e.target.value)}
                  placeholder="AUSTIN"
                  maxLength={25}
                  className={inputClass}
                />
              </FormField>
              <FormField label="State (2-letter)">
                <input
                  type="text"
                  value={form.merchant_state}
                  onChange={(e) => handleChange("merchant_state", e.target.value.toUpperCase())}
                  placeholder="TX"
                  maxLength={2}
                  className={inputClass}
                />
              </FormField>
              <FormField label="ZIP Code">
                <input
                  type="text"
                  value={form.merchant_zip}
                  onChange={(e) => handleChange("merchant_zip", e.target.value)}
                  placeholder="78701"
                  maxLength={10}
                  className={inputClass}
                />
              </FormField>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Processing Authorization..." : "Submit Authorization Request"}
          </button>
        </form>
      )}
    </div>
  );
}
