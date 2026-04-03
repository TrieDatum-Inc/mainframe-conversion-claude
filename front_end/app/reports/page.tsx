/**
 * Transaction Reports page — CORPT00C / Transaction CR00 equivalent.
 *
 * CORPT00C flow:
 *   First entry: display report type selection form
 *   Re-entry: validate selection → prompt for confirmation (CONFIRM field)
 *   CONFIRM=Y: submit job to TDQ JOBS → modern: POST /reports
 *
 * BMS screen: CORPT00 / CORPT0A
 *   Row 4:  "Transaction Reports" heading (bright, neutral)
 *   Row 7:  MONTHLY radio field (GREEN, IC cursor home)
 *   Row 9:  YEARLY radio field (GREEN)
 *   Row 11: CUSTOM radio field (GREEN)
 *   Row 13: Start Date MM/DD/YYYY fields (SDTMM, SDTDD, SDTYYYY)
 *   Row 14: End Date MM/DD/YYYY fields (EDTMM, EDTDD, EDTYYYY)
 *   Row 19: CONFIRM field (Y/N)
 *   Row 23: ERRMSG (RED/GREEN)
 *   Row 24: ENTER=Continue  F3=Back
 */
import type { Metadata } from "next";
import { ReportsClient } from "./ReportsClient";

export const metadata: Metadata = {
  title: "Transaction Reports — CardDemo (CR00)",
  description: "CardDemo Transaction Reports — CORPT00C equivalent",
};

export default function ReportsPage() {
  return <ReportsClient />;
}
