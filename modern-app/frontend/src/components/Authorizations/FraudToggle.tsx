"use client";

/**
 * FraudToggle Component
 *
 * Mark/Remove fraud flag on an authorization record.
 * Maps to COPAUS1C F5 key → EXEC CICS LINK COPAUS2C behavior.
 *
 * UI Pattern:
 * - If fraud_status is NULL or 'R': show "Mark as Fraud" button (red)
 * - If fraud_status is 'F': show "Remove Fraud Flag" button (yellow)
 * - Confirmation dialog before action (replaces COBOL Y/N confirm pattern)
 *
 * COBOL COPAUS2C return status mapping:
 *   WS-FRD-UPDT-SUCCESS ('S') → success toast
 *   WS-FRD-UPDT-FAILED  ('F') → error message
 */

import { useState } from "react";
import { toggleFraud } from "@/lib/api";

interface FraudToggleProps {
  detailId: number;
  currentFraudStatus: "F" | "R" | null;
  onSuccess?: () => void;
}

export function FraudToggle({ detailId, currentFraudStatus, onSuccess }: FraudToggleProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const isFraud = currentFraudStatus === "F";
  const action = isFraud ? "remove" : "mark";
  const buttonLabel = isFraud ? "F5 Remove Fraud Flag" : "F5 Mark as Fraud";
  const confirmMessage = isFraud
    ? "Remove the fraud flag from this authorization?"
    : "Mark this authorization as FRAUD? This will create a fraud record.";

  const handleConfirm = async () => {
    setLoading(true);
    setError(null);
    setShowConfirm(false);

    try {
      const result = await toggleFraud(detailId, { action });
      if (result.success) {
        setSuccessMessage(result.message);
        onSuccess?.();
        setTimeout(() => setSuccessMessage(null), 3000);
      } else {
        setError(`Action failed: ${result.message}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fraud action failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative">
      {/* Main button */}
      <button
        onClick={() => setShowConfirm(true)}
        disabled={loading}
        className={`px-4 py-2 text-sm font-medium rounded-md border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
          isFraud
            ? "bg-yellow-50 text-yellow-800 border-yellow-400 hover:bg-yellow-100"
            : "bg-red-50 text-red-800 border-red-400 hover:bg-red-100"
        }`}
      >
        {loading ? "Processing..." : buttonLabel}
      </button>

      {/* Success message */}
      {successMessage && (
        <div className="mt-2 text-xs text-green-700 bg-green-50 border border-green-200 rounded px-3 py-2">
          {successMessage}
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="mt-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
          {error}
        </div>
      )}

      {/* Confirmation dialog */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
          <div className="bg-white rounded-lg shadow-xl border border-gray-200 p-6 max-w-sm w-full mx-4">
            <h3 className="text-base font-semibold text-gray-900 mb-3">
              Confirm Fraud Action
            </h3>
            <p className="text-sm text-gray-600 mb-5">{confirmMessage}</p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel (N)
              </button>
              <button
                onClick={handleConfirm}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  isFraud
                    ? "bg-yellow-600 text-white hover:bg-yellow-700"
                    : "bg-red-600 text-white hover:bg-red-700"
                }`}
              >
                Confirm (Y)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
