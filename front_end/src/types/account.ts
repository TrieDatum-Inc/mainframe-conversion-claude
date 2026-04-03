/**
 * TypeScript types mirroring the FastAPI Pydantic schemas.
 * Derived from CVACT01Y, CVCUS01Y, CVACT02Y, CVACT03Y copybooks.
 */

export interface CardInfo {
  card_num: string;
  card_embossed_name: string | null;
  card_expiration_date: string | null; // ISO date string
  card_active_status: "Y" | "N";
}

export interface CustomerInfo {
  cust_id: string;
  cust_first_name: string | null;
  cust_middle_name: string | null;
  cust_last_name: string | null;
  cust_addr_line_1: string | null;
  cust_addr_line_2: string | null;
  cust_addr_line_3: string | null;
  cust_addr_state_cd: string | null;
  cust_addr_country_cd: string | null;
  cust_addr_zip: string | null;
  cust_phone_num_1: string | null;
  cust_phone_num_2: string | null;
  ssn_formatted: string | null; // XXX-XX-XXXX
  cust_govt_issued_id: string | null;
  cust_dob: string | null; // ISO date string
  cust_eft_account_id: string | null;
  cust_pri_card_holder_ind: "Y" | "N" | null;
  cust_fico_credit_score: number | null;
  updated_at: string | null;
}

/** Response from GET /api/accounts/{acct_id} */
export interface AccountDetailResponse {
  acct_id: string;
  acct_active_status: "Y" | "N";
  acct_curr_bal: number;
  acct_credit_limit: number;
  acct_cash_credit_limit: number;
  acct_open_date: string | null; // ISO date
  acct_expiration_date: string | null;
  acct_reissue_date: string | null;
  acct_curr_cyc_credit: number;
  acct_curr_cyc_debit: number;
  acct_addr_zip: string | null;
  acct_group_id: string | null;
  updated_at: string; // ISO datetime — used as concurrency token
  customer: CustomerInfo | null;
  cards: CardInfo[];
}

/** Phone number split into 3 parts (CACTUPA screen fields ACSPH1A/B/C) */
export interface PhoneInput {
  area_code: string; // 3 digits
  prefix: string;    // 3 digits
  line_number: string; // 4 digits
}

/** SSN split into 3 parts (CACTUPA screen fields ACTSSN1/2/3) */
export interface SsnInput {
  part1: string; // 3 digits
  part2: string; // 2 digits
  part3: string; // 4 digits
}

/** Request body for PUT /api/accounts/{acct_id} */
export interface AccountUpdateRequest {
  updated_at: string; // ISO datetime — optimistic concurrency token

  // Account fields
  acct_active_status: "Y" | "N";
  acct_credit_limit: number;
  acct_cash_credit_limit: number;
  acct_curr_bal: number;
  acct_curr_cyc_credit: number;
  acct_curr_cyc_debit: number;
  acct_open_date: string | null;
  acct_expiration_date: string | null;
  acct_reissue_date: string | null;
  acct_group_id: string | null;

  // Customer fields
  cust_first_name: string;
  cust_middle_name: string | null;
  cust_last_name: string;
  cust_addr_line_1: string;
  cust_addr_line_2?: string | null;
  cust_addr_line_3?: string | null;
  cust_addr_state_cd: string;
  cust_addr_country_cd: string;
  cust_addr_zip: string;
  cust_phone_num_1: PhoneInput;
  cust_phone_num_2?: PhoneInput | null;
  cust_ssn: SsnInput;
  cust_govt_issued_id?: string | null;
  cust_dob: string; // ISO date
  cust_eft_account_id: string;
  cust_pri_card_holder_ind: "Y" | "N";
  cust_fico_credit_score: number;
}

export interface AccountUpdateResponse {
  message: string;
  acct_id: string;
  updated_at: string;
}

export type ApiError = {
  detail: string | { msg: string; loc: string[] }[];
};
