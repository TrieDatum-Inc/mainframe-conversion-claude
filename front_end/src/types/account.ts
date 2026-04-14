/**
 * Account module TypeScript types.
 *
 * COBOL origin:
 *   AccountViewResponse  → COACTVWC (Transaction CAVW) / COACTVW BMS mapset
 *   AccountUpdateRequest → COACTUPC (Transaction CAUP) / COACTUP BMS mapset
 *
 * All financial amounts are strings in JSON (Python Decimal serializes as string)
 * to avoid floating-point precision loss.
 */

/**
 * Customer details section of the account view/update response.
 * Maps BMS screen rows 11-20 of COACTVW (all ASKIP/output-only in view).
 */
export interface CustomerDetail {
  /** ACSTNUM — 9-digit customer identifier */
  customer_id: number;
  /**
   * ACSTSSN — SSN masked as "***-**-XXXX" (last 4 digits only).
   * SECURITY: Full SSN is never returned by the API. Do not attempt
   * to unmask or reconstruct it client-side.
   */
  ssn_masked: string;
  /** ACSTDOB — ISO date string YYYY-MM-DD or null */
  date_of_birth: string | null;
  /** ACSTFCO — FICO credit score (300–850) or null */
  fico_score: number | null;
  /** ACSFNAM X(25) */
  first_name: string;
  /** ACSMNAM X(25) */
  middle_name: string | null;
  /** ACSLNAM X(25) */
  last_name: string;
  /** ACSADL1 X(50) */
  address_line_1: string | null;
  /** ACSADL2 X(50) */
  address_line_2: string | null;
  /** ACSCITY X(50) */
  city: string | null;
  /** ACSSTTE X(2) */
  state_code: string | null;
  /** ACSZIPC X(10) */
  zip_code: string | null;
  /** ACSCTRY X(3) */
  country_code: string | null;
  /** ACSPHN1 — single field NNN-NNN-NNNN (combines ACSPH1A/B/C from update screen) */
  phone_1: string | null;
  /** ACSPHN2 */
  phone_2: string | null;
  /** ACSGOVT X(20) */
  government_id_ref: string | null;
  /** ACSEFTC X(10) */
  eft_account_id: string | null;
  /** ACSPFLG X(1) — Y or N */
  primary_card_holder: "Y" | "N";
}

/**
 * Full account view response from GET /api/v1/accounts/{account_id}.
 * Maps COACTVWC display screen (COACTVW BMS mapset, map CACTVWA).
 * All fields are output-only (ASKIP) except the search account_id.
 *
 * Financial amounts: Decimal serialized as strings in JSON to preserve precision.
 * Format for display: +$X,XXX,XXX.XX or -$X,XXX,XXX.XX using Intl.NumberFormat.
 */
export interface AccountViewResponse {
  /** ACCTSID — 11-digit account number */
  account_id: number;
  /** ACSTTUS X(1) — Y=Active, N=Inactive */
  active_status: "Y" | "N";
  /** ADTOPEN — ISO date string or null */
  open_date: string | null;
  /** AEXPDT — ISO date string or null */
  expiration_date: string | null;
  /** AREISDT — ISO date string or null */
  reissue_date: string | null;
  /** ACRDLIM — PICOUT='+ZZZ,ZZZ,ZZZ.99' in BMS; Decimal as string in JSON */
  credit_limit: string;
  /** ACSHLIM */
  cash_credit_limit: string;
  /** ACURBAL */
  current_balance: string;
  /** ACRCYCR */
  curr_cycle_credit: string;
  /** ACRCYDB */
  curr_cycle_debit: string;
  /** AADDGRP X(10) */
  group_id: string | null;
  /** Customer details section (rows 11-20 of BMS screen) */
  customer: CustomerDetail;
}

/**
 * Customer fields in the account update request.
 * Maps COACTUPC editable customer fields (COACTUP BMS mapset, all UNPROT).
 *
 * SSN is submitted as three separate parts matching ACTSSN1/ACTSSN2/ACTSSN3
 * BMS split fields. The backend assembles them as NNN-NN-NNNN for storage.
 */
export interface CustomerUpdateRequest {
  /** ACSTNUM — must match the customer linked to this account */
  customer_id: number;
  /** ACSFNAM X(25) — alpha/space/hyphen/apostrophe only */
  first_name: string;
  /** ACSMNAM X(25) */
  middle_name?: string;
  /** ACSLNAM X(25) */
  last_name: string;
  /** ACSADL1 X(50) */
  address_line_1?: string;
  /** ACSADL2 X(50) */
  address_line_2?: string;
  /** ACSCITY X(50) */
  city?: string;
  /** ACSSTTE X(2) */
  state_code?: string;
  /** ACSZIPC X(10) */
  zip_code?: string;
  /** ACSCTRY X(3) */
  country_code?: string;
  /** ACSPH1A/B/C combined — NNN-NNN-NNNN format */
  phone_1?: string;
  /** ACSPH2A/B/C combined */
  phone_2?: string;
  /** ACTSSN1 — 3-digit area number; cannot be 000, 666, or 900-999 */
  ssn_part1: string;
  /** ACTSSN2 — 2-digit group number */
  ssn_part2: string;
  /** ACTSSN3 — 4-digit serial number */
  ssn_part3: string;
  /** DOBYEAR/DOBMON/DOBDAY combined — ISO date string YYYY-MM-DD */
  date_of_birth: string;
  /** ACSTFCO — 300–850 range */
  fico_score?: number;
  /** ACSGOVT X(20) */
  government_id_ref?: string;
  /** ACSEFTC X(10) */
  eft_account_id?: string;
  /** ACSPFLG X(1) — Y or N */
  primary_card_holder: "Y" | "N";
}

/**
 * Account update request body for PUT /api/v1/accounts/{account_id}.
 * Maps COACTUPC editable fields (COACTUP BMS mapset, all UNPROT).
 *
 * Dates are ISO strings (YYYY-MM-DD) combining the split year/month/day
 * BMS sub-fields (e.g. OPNYEAR + OPNMON + OPNDAY → open_date).
 * Financial amounts are numbers (converted from form string inputs).
 */
export interface AccountUpdateRequest {
  /** ACSTTUS X(1) — Y or N */
  active_status: "Y" | "N";
  /** OPNYEAR/OPNMON/OPNDAY combined */
  open_date: string;
  /** EXPYEAR/EXPMON/EXPDAY combined */
  expiration_date: string;
  /** RISYEAR/RISMON/RISDAY combined */
  reissue_date: string;
  /** ACRDLIM X(15) — must be >= 0 */
  credit_limit: number;
  /** ACSHLIM X(15) — must be >= 0 and <= credit_limit */
  cash_credit_limit: number;
  /** ACURBAL X(15) — can be negative */
  current_balance: number;
  /** ACRCYCR X(15) — must be >= 0 */
  curr_cycle_credit: number;
  /** ACRCYDB X(15) — must be >= 0 */
  curr_cycle_debit: number;
  /** AADDGRP X(10) */
  group_id?: string;
  customer: CustomerUpdateRequest;
}
