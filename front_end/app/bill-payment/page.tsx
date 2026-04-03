/**
 * Bill Payment page — COBIL00C / Transaction CB00 equivalent.
 *
 * COBIL00C flow:
 *   First entry: display account ID input form
 *   Enter key (no confirm): READ-ACCTDAT-FILE → display CURBAL
 *   CONFIRM=Y: process payment (write transaction + zero balance)
 *   CONFIRM=N: CLEAR-CURRENT-SCREEN (re-initialize all fields)
 *   PF3: Back to main menu
 *   PF4: Clear current screen
 *
 * BMS screen: COBIL00 / COBIL0A
 *   Row 4:  "Bill Payment" heading (BRT, NEUTRAL)
 *   Row 6:  "Enter Acct ID:" [ACTIDIN (11 chars, IC)] — GREEN
 *   Row 8:  horizontal rule (dashes) — YELLOW
 *   Row 11: "Your current balance is:" [CURBAL (14 chars, ASKIP)] — TURQUOISE/BLUE
 *   Row 15: "Do you want to pay your balance now. Please confirm:" [CONFIRM] (Y/N)
 *   Row 23: [ERRMSG] — RED/GREEN
 *   Row 24: ENTER=Continue  F3=Back  F4=Clear
 */
import type { Metadata } from "next";
import { BillPaymentClient } from "./BillPaymentClient";

export const metadata: Metadata = {
  title: "Bill Payment — CardDemo (CB00)",
  description: "CardDemo Bill Payment — COBIL00C equivalent",
};

export default function BillPaymentPage() {
  return <BillPaymentClient />;
}
