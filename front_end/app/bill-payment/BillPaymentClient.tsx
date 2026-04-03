"use client";

/**
 * BillPaymentClient — maps COBIL00 BMS screen (COBIL0A map).
 *
 * BMS screen layout reference:
 *   Row 4:  "Bill Payment" heading (BRT, NEUTRAL)
 *   Row 6:  "Enter Acct ID:" [ACTIDIN (11 chars, IC, UNPROT)] — GREEN
 *   Row 8:  "---...---" horizontal rule — YELLOW
 *   Row 11: "Your current balance is:" [CURBAL (ASKIP, protected)] — TURQUOISE/BLUE
 *   Row 15: "Do you want to pay your balance now. Please confirm:" [CONFIRM (Y/N)]
 *   Row 23: [ERRMSG] — ASKIP,BRT,FSET,RED (error) or GREEN (success)
 *   Row 24: ENTER=Continue  F3=Back  F4=Clear
 *
 * Two-phase flow:
 *   Phase 1: Enter account ID → ENTER → GET /payments/balance/{acct_id} → display CURBAL
 *   Phase 2: CONFIRM=Y → POST /payments/{acct_id} → success message (GREEN)
 *            CONFIRM=N → CLEAR-CURRENT-SCREEN (INITIALIZE-ALL-FIELDS)
 *            CONFIRM other → 'Invalid value. Valid values are (Y/N)...'
 *
 * Business rules:
 *   BR-001: Account ID must not be empty
 *   BR-003: Balance <= 0 → 'You have nothing to pay...' (info, not hard error)
 *   BR-004: Payment is always for full balance
 *   BR-009: Confirmation required
 */
import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";

import { getAccountBalance, processPayment } from "@/lib/api";
import { ScreenHeader } from "@/components/ui/ScreenHeader";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { PFKeyBar } from "@/components/ui/PFKeyBar";
import { getErrorMessage } from "@/lib/utils";
import type { AccountBalanceResponse, MessageType, PaymentResponse } from "@/types";

// ============================================================
// Helper: format currency for CURBAL display field
// ============================================================
function formatBalance(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

// ============================================================
// Phase constants — maps COBIL00C two-stage logic
// ============================================================
type Phase = "enter_acct" | "confirm_payment" | "payment_done";

export function BillPaymentClient() {
  const router = useRouter();
  const acctInputRef = useRef<HTMLInputElement>(null);
  const confirmInputRef = useRef<HTMLInputElement>(null);

  // Phase 1 fields — ACTIDIN
  const [acctId, setAcctId] = useState<string>("");
  const [phase, setPhase] = useState<Phase>("enter_acct");

  // Phase 1 result — CURBAL display
  const [balanceData, setBalanceData] = useState<AccountBalanceResponse | null>(null);

  // Phase 2 field — CONFIRMI
  const [confirmValue, setConfirmValue] = useState<string>("");

  // Payment result — final success state
  const [paymentResult, setPaymentResult] = useState<PaymentResponse | null>(null);

  // Status messages — WS-MESSAGE / ERRMSG
  const [message, setMessage] = useState<string | null>(null);
  const [messageType, setMessageType] = useState<MessageType>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Auto-focus on acct input on mount — mirrors ACTIDINL = -1 (cursor home)
  useEffect(() => {
    acctInputRef.current?.focus();
  }, []);

  // Auto-focus on confirm input when phase changes
  useEffect(() => {
    if (phase === "confirm_payment") {
      confirmInputRef.current?.focus();
    }
  }, [phase]);

  // ============================================================
  // INITIALIZE-ALL-FIELDS equivalent — PF4 and CONFIRM=N
  // ============================================================
  function initializeAllFields() {
    setAcctId("");
    setConfirmValue("");
    setBalanceData(null);
    setPaymentResult(null);
    setMessage(null);
    setMessageType(null);
    setPhase("enter_acct");
    setTimeout(() => acctInputRef.current?.focus(), 50);
  }

  // ============================================================
  // Phase 1: READ-ACCTDAT-FILE — display CURBAL
  // ============================================================
  async function handleAccountLookup() {
    const cleanAcctId = acctId.trim();

    // BR-001: Account ID must not be empty
    if (!cleanAcctId) {
      setMessage("Acct ID can NOT be empty...");
      setMessageType("error");
      acctInputRef.current?.focus();
      return;
    }

    setIsLoading(true);
    setMessage(null);
    try {
      const data = await getAccountBalance(cleanAcctId);
      setBalanceData(data);
      setPhase("confirm_payment");

      // BR-003: Zero/negative balance — show info message, not hard error
      if (data.message) {
        setMessage(data.message);
        setMessageType(data.message_type ?? "info");
      }
    } catch (err) {
      const e = err as Record<string, unknown>;
      if ((e.status as number) === 401) {
        router.push("/login");
        return;
      }
      setMessage(getErrorMessage(err));
      setMessageType("error");
    } finally {
      setIsLoading(false);
    }
  }

  // ============================================================
  // Phase 2: EVALUATE CONFIRMI — process or cancel payment
  // ============================================================
  async function handleConfirm() {
    const confirm = confirmValue.trim().toUpperCase();

    // COBIL00C EVALUATE CONFIRMI (lines 173-191)
    if (confirm === "N") {
      // WHEN 'N' or 'n' → CLEAR-CURRENT-SCREEN
      initializeAllFields();
      return;
    }

    if (confirm !== "Y") {
      // WHEN OTHER → 'Invalid value. Valid values are (Y/N)...'
      setMessage("Invalid value. Valid values are (Y/N)...");
      setMessageType("error");
      confirmInputRef.current?.focus();
      return;
    }

    // WHEN 'Y' or 'y' → CONF-PAY-YES = TRUE → process payment
    if (!balanceData) return;

    setIsLoading(true);
    setMessage(null);
    try {
      const result = await processPayment(balanceData.acct_id);
      setPaymentResult(result);
      setPhase("payment_done");
      // WRITE-TRANSACT-FILE success: green message
      // 'Payment successful. Your Transaction ID is <TRAN-ID>.'
      setMessage(result.message);
      setMessageType("success");
      // INITIALIZE-ALL-FIELDS after success
      setAcctId("");
      setConfirmValue("");
    } catch (err) {
      const e = err as Record<string, unknown>;
      if ((e.status as number) === 401) {
        router.push("/login");
        return;
      }
      setMessage(getErrorMessage(err));
      setMessageType("error");
    } finally {
      setIsLoading(false);
    }
  }

  // ============================================================
  // ENTER key handler — dispatches to correct phase
  // ============================================================
  function handleEnter(e: React.FormEvent) {
    e.preventDefault();
    if (phase === "enter_acct" || (phase === "payment_done" && !acctId)) {
      handleAccountLookup();
    } else if (phase === "confirm_payment") {
      handleConfirm();
    } else if (phase === "payment_done") {
      // User entered new account ID after payment — start fresh lookup
      initializeAllFields();
      setTimeout(() => handleAccountLookup(), 50);
    }
  }

  // PF3=Back — XCTL to COMEN01C (main menu or calling program)
  function handleBack() {
    router.push("/main-menu");
  }

  // PF4=Clear — CLEAR-CURRENT-SCREEN equivalent
  function handleClear() {
    initializeAllFields();
  }

  const showBalance = phase === "confirm_payment" || phase === "payment_done";
  const showConfirmField = phase === "confirm_payment" && balanceData && balanceData.curr_bal > 0;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col font-mono">
      {/* Header — POPULATE-HEADER-INFO equivalent */}
      <ScreenHeader
        transactionId="CB00"
        programName="COBIL00C"
        title01="AWS Mainframe Modernization"
        title02="CardDemo"
      />

      {/* Main screen content */}
      <main className="flex-1 p-4 max-w-3xl mx-auto w-full">
        {/* Row 4: Screen heading — BRT, NEUTRAL */}
        <h1 className="text-center text-white font-bold text-lg mb-6 mt-2">
          Bill Payment
        </h1>

        <form onSubmit={handleEnter} noValidate>
          {/* Row 6: Enter Acct ID — ACTIDIN (IC, GREEN) */}
          <div className="mb-4 flex items-center gap-3">
            <label
              htmlFor="acct-id"
              className="text-green-400 w-32 text-sm"
            >
              Enter Acct ID:
            </label>
            <input
              id="acct-id"
              ref={acctInputRef}
              type="text"
              value={acctId}
              onChange={(e) => {
                setAcctId(e.target.value);
                if (phase === "payment_done") {
                  setPhase("enter_acct");
                  setBalanceData(null);
                  setPaymentResult(null);
                  setMessage(null);
                }
              }}
              maxLength={11}
              pattern="[0-9]*"
              inputMode="numeric"
              disabled={isLoading || phase === "confirm_payment"}
              className="bg-gray-800 border border-green-600 text-green-400 font-mono px-2 py-1 rounded w-40 focus:outline-none focus:ring-1 focus:ring-green-500 underline disabled:border-gray-600 disabled:text-gray-500"
              aria-label="Account ID (up to 11 digits)"
              autoComplete="off"
            />
          </div>

          {/* Row 8: Horizontal rule — YELLOW */}
          <div className="border-b border-yellow-600 mb-4 opacity-50" />

          {/* Row 11: Current balance display — CURBAL (ASKIP, protected, BLUE) */}
          {showBalance && balanceData && (
            <div className="mb-6">
              <div className="flex items-center gap-3">
                <span className="text-cyan-400 text-sm">
                  Your current balance is:
                </span>
                <span
                  className={`font-bold text-lg ${
                    balanceData.curr_bal > 0
                      ? "text-blue-300"
                      : "text-yellow-400"
                  }`}
                  aria-label={`Current balance: ${formatBalance(balanceData.curr_bal)}`}
                >
                  {formatBalance(balanceData.curr_bal)}
                </span>
              </div>
            </div>
          )}

          {/* Payment result display */}
          {phase === "payment_done" && paymentResult && (
            <div className="mb-4 bg-gray-800 p-3 rounded border border-green-600 text-sm">
              <p className="text-green-400 font-bold">Payment Processed:</p>
              <p className="text-gray-300">
                Transaction ID:{" "}
                <span className="text-white font-bold">
                  {paymentResult.tran_id}
                </span>
              </p>
              <p className="text-gray-300">
                Amount Paid:{" "}
                <span className="text-white">
                  {formatBalance(paymentResult.payment_amount)}
                </span>
              </p>
              <p className="text-gray-300">
                New Balance:{" "}
                <span className="text-white">
                  {formatBalance(paymentResult.new_balance)}
                </span>
              </p>
            </div>
          )}

          {/* Row 15: Confirmation prompt — CONFIRM (Y/N) */}
          {showConfirmField && (
            <div className="mb-4 flex items-center gap-3">
              <span className="text-cyan-400 text-sm flex-shrink-0">
                Do you want to pay your balance now. Please confirm:
              </span>
              <input
                id="confirm-input"
                ref={confirmInputRef}
                type="text"
                value={confirmValue}
                onChange={(e) =>
                  setConfirmValue(e.target.value.slice(0, 1).toUpperCase())
                }
                maxLength={1}
                disabled={isLoading}
                className="bg-gray-800 border border-green-600 text-green-400 font-mono px-2 py-1 rounded w-10 text-center focus:outline-none focus:ring-1 focus:ring-green-500 underline disabled:border-gray-600"
                aria-label="Confirm payment Y or N"
                autoComplete="off"
              />
              <span className="text-gray-400 text-xs">(Y/N)</span>
            </div>
          )}

          {/* Quick Y/N buttons — accessibility enhancement for confirm phase */}
          {showConfirmField && (
            <div className="mb-4 flex gap-3">
              <button
                type="button"
                onClick={() => {
                  setConfirmValue("Y");
                  setTimeout(() => handleConfirm(), 50);
                }}
                disabled={isLoading}
                className="bg-green-800 hover:bg-green-700 disabled:bg-gray-700 text-white font-mono py-1 px-4 rounded text-sm transition-colors"
                aria-label="Confirm payment Yes"
              >
                {isLoading ? "Processing..." : "Y — Pay Now"}
              </button>
              <button
                type="button"
                onClick={() => initializeAllFields()}
                disabled={isLoading}
                className="bg-red-900 hover:bg-red-800 disabled:bg-gray-700 text-white font-mono py-1 px-4 rounded text-sm transition-colors"
                aria-label="Cancel payment No"
              >
                N — Cancel
              </button>
            </div>
          )}

          {/* ENTER button */}
          {phase !== "confirm_payment" && (
            <div className="mb-4">
              <button
                type="submit"
                disabled={isLoading}
                className="bg-blue-800 hover:bg-blue-700 disabled:bg-gray-700 text-white font-mono py-2 px-6 rounded transition-colors"
                aria-label="Continue (ENTER key)"
              >
                {isLoading ? "Loading..." : "ENTER — Continue"}
              </button>
            </div>
          )}
        </form>

        {/* Row 23: ERRMSG */}
        <ErrorMessage message={message} messageType={messageType} />
      </main>

      {/* Row 24: PF key legend */}
      <PFKeyBar
        keys={[
          { key: "ENTER", label: "Continue" },
          { key: "F3", label: "Back", onClick: handleBack },
          { key: "F4", label: "Clear", onClick: handleClear },
        ]}
      />
    </div>
  );
}
