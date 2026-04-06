/**
 * TypeScript interfaces matching the FastAPI Pydantic schemas.
 *
 * COBOL origin: Maps USRSEC VSAM KSDS fields (CSUSR01Y copybook)
 * and COUSR BMS map field types to TypeScript.
 *
 * Security: password_hash is NEVER included in any response type.
 */

// ---------------------------------------------------------------------------
// User types — maps CSUSR01Y copybook fields
// ---------------------------------------------------------------------------

/**
 * User type values.
 * COBOL origin: SEC-USR-TYPE X(01) — 'A'=Admin, 'U'=Regular
 */
export type UserType = 'A' | 'U';

/**
 * User response from GET /api/v1/users and GET /api/v1/users/{user_id}.
 * Password is NEVER included.
 *
 * COBOL origin: COUSR0AO output map fields: USRID1O, FNAME1O, LNAME1O, UTYPE1O
 */
export interface UserResponse {
  user_id: string;        // SEC-USR-ID X(08)
  first_name: string;     // SEC-USR-FNAME X(20)
  last_name: string;      // SEC-USR-LNAME X(20)
  user_type: UserType;    // SEC-USR-TYPE X(01)
  created_at: string;     // ISO datetime (not in original VSAM)
  updated_at: string;     // ISO datetime (not in original VSAM)
}

/**
 * Paginated user list response from GET /api/v1/users.
 *
 * COBOL origin: COUSR00C POPULATE-USER-DATA output state:
 *   items           → rows displayed (USRID1O–USRID10O, FNAME1O–FNAME10O, etc.)
 *   has_next        → CDEMO-CU00-NEXT-PAGE-FLG
 *   first_item_key  → CDEMO-CU00-USRID-FIRST
 *   last_item_key   → CDEMO-CU00-USRID-LAST
 */
export interface UserListResponse {
  items: UserResponse[];
  page: number;
  page_size: number;
  total_count: number;
  has_next: boolean;
  has_previous: boolean;
  first_item_key: string | null;
  last_item_key: string | null;
}

/**
 * Request body for POST /api/v1/users.
 *
 * COBOL origin: COUSR01C COUSR1AI input map fields:
 *   FNAMEI, LNAMEI, USERIDI, PASSWDI, USRTYPEI — all required
 */
export interface UserCreateRequest {
  user_id: string;      // USERIDI (max 8 chars, alphanumeric)
  first_name: string;   // FNAMEI (max 20 chars, non-blank)
  last_name: string;    // LNAMEI (max 20 chars, non-blank)
  password: string;     // PASSWDI (required on create)
  user_type: UserType;  // USRTYPEI ('A' or 'U')
}

/**
 * Request body for PUT /api/v1/users/{user_id}.
 *
 * COBOL origin: COUSR02C COUSR2AI editable fields (user_id not editable):
 *   FNAMEI, LNAMEI, PASSWDI (optional), USRTYPEI
 */
export interface UserUpdateRequest {
  first_name: string;
  last_name: string;
  password?: string;    // Optional — blank means no password change
  user_type: UserType;
}

// ---------------------------------------------------------------------------
// Common API types
// ---------------------------------------------------------------------------

export interface ApiErrorResponse {
  error_code: string;
  message: string;
  details: Array<{ field?: string; message: string }>;
}

export interface MessageResponse {
  message: string;
}

export interface PaginationParams {
  page: number;
  page_size: number;
  user_id_filter?: string;
}

// ---------------------------------------------------------------------------
// Transaction Type types — maps CARDDEMO.TRANSACTION_TYPE DB2 table
// COBOL origin: COTRTLIC (list/update/delete) + COTRTUPC (add/update/delete)
// ---------------------------------------------------------------------------

/**
 * Transaction type response from GET /api/v1/transaction-types and related endpoints.
 *
 * COBOL origin: DCLTRTYP DCLGEN fields:
 *   DCL-TR-TYPE         CHAR(2)     → type_code
 *   DCL-TR-DESCRIPTION  VARCHAR(50) → description
 *   updated_at is added for optimistic locking (replaces COTRTLIC WS-DATACHANGED-FLAG)
 */
export interface TransactionTypeResponse {
  type_code: string;    // TR_TYPE CHAR(2) — 2-digit numeric, e.g. '01'
  description: string;  // TR_DESCRIPTION VARCHAR(50) — alphanumeric only
  created_at: string;   // ISO datetime (not in original DB2 table)
  updated_at: string;   // ISO datetime — used as optimistic lock version on PUT
}

/**
 * Paginated transaction type list response from GET /api/v1/transaction-types.
 *
 * COBOL origin: COTRTLIC WS-CA-ALL-ROWS-OUT (7 rows per page, WS-MAX-SCREEN-LINES=7).
 *   has_next        → CA-NEXT-PAGE-EXISTS
 *   first_item_key  → WS-CA-FIRST-TR-CODE (backward cursor anchor)
 *   last_item_key   → WS-CA-LAST-TR-CODE (forward cursor anchor)
 */
export interface TransactionTypeListResponse {
  items: TransactionTypeResponse[];
  page: number;
  page_size: number;
  total_count: number;
  has_next: boolean;
  has_previous: boolean;
  first_item_key: string | null;
  last_item_key: string | null;
}

/**
 * Request body for POST /api/v1/transaction-types.
 *
 * COBOL origin: COTRTUPC TTUP-CREATE-NEW-RECORD state.
 *   TRTYPCD → type_code (numeric 01-99, non-zero per 1210-EDIT-TRANTYPE)
 *   TRTYDSC → description (alphanumeric per 1230-EDIT-ALPHANUM-REQD)
 */
export interface TransactionTypeCreateRequest {
  type_code: string;    // 1-2 digit numeric string, e.g. '01', '15'
  description: string;  // Alphanumeric + spaces, max 50 chars
}

/**
 * Request body for PUT /api/v1/transaction-types/{type_code}.
 *
 * COBOL origin: COTRTUPC 9600-WRITE-PROCESSING (UPDATE path).
 * Only description is editable — type_code is protected on both screens.
 * optimistic_lock_version replaces COTRTLIC WS-DATACHANGED-FLAG.
 */
export interface TransactionTypeUpdateRequest {
  description: string;                // New description
  optimistic_lock_version: string;   // updated_at from GET — ISO datetime string
}

/**
 * Query parameters for GET /api/v1/transaction-types.
 *
 * COBOL origin: COTRTLIC filter fields TRTYPE (type code filter) and TRDESC (description filter).
 */
export interface TransactionTypeListParams {
  page?: number;
  page_size?: number;
  type_code_filter?: string;
  description_filter?: string;
}

// ---------------------------------------------------------------------------
// Account types — maps ACCTDAT VSAM KSDS + CUSTDAT VSAM KSDS
// COBOL origin: COACTVWC (view), COACTUPC (update)
// BMS maps: CACTVWA (view), CACTUPA (update)
// ---------------------------------------------------------------------------

/**
 * Customer detail embedded in account view response.
 * Maps rows 11-20 of CACTVWA BMS map (all ASKIP — read-only).
 * SSN is masked: ***-**-XXXX (never expose plain SSN).
 */
export interface CustomerDetailResponse {
  customer_id: number;          // ACSTNUM — CUST-ID 9(9)
  ssn_masked: string;           // ACSTSSN — masked per PCI-DSS: ***-**-XXXX
  date_of_birth: string | null; // ACSTDOB — CUST-DOB-YYYY-MM-DD
  fico_score: number | null;    // ACSTFCO — CUST-FICO-CREDIT-SCORE 9(3); 300-850
  first_name: string;           // ACSFNAM — CUST-FIRST-NAME X(25)
  middle_name: string | null;   // ACSMNAM — CUST-MIDDLE-NAME X(25)
  last_name: string;            // ACSLNAM — CUST-LAST-NAME X(25)
  address_line_1: string | null; // ACSADL1 — CUST-ADDR-LINE-1 X(50)
  address_line_2: string | null; // ACSADL2
  city: string | null;          // ACSCITY
  state_code: string | null;    // ACSSTTE — CUST-ADDR-STATE-CD X(2)
  zip_code: string | null;      // ACSZIPC
  country_code: string | null;  // ACSCTRY — CUST-ADDR-COUNTRY-CD X(3)
  phone_1: string | null;       // ACSPHN1 — single field in view; split in update
  phone_2: string | null;       // ACSPHN2
  government_id_ref: string | null; // ACSGOVT — CUST-GOVT-ISSUED-ID X(20)
  eft_account_id: string | null; // ACSEFTC — CUST-EFT-ACCOUNT-ID X(10)
  primary_card_holder: string;  // ACSPFLG — CUST-PRI-CARD-HOLDER-IND X(1); Y/N
}

/**
 * Account view response — maps all CACTVWA display fields.
 * COACTVWC joins: ACCTDAT + CUSTDAT (via xref) + CARDAIX.
 * Currency amounts formatted with PICOUT='+ZZZ,ZZZ,ZZZ.99' equivalent.
 */
export interface AccountViewResponse {
  account_id: number;                // ACCTSID — ACCT-ID 9(11)
  active_status: string;             // ACSTTUS — ACCT-ACTIVE-STATUS X(1); Y/N
  open_date: string | null;          // ADTOPEN — ACCT-OPEN-DATE
  expiration_date: string | null;    // AEXPDT — ACCT-EXPIRAION-DATE
  reissue_date: string | null;       // AREISDT — ACCT-REISSUE-DATE
  credit_limit: string;              // ACRDLIM — PICOUT='+ZZZ,ZZZ,ZZZ.99'
  cash_credit_limit: string;         // ACSHLIM
  current_balance: string;           // ACURBAL
  curr_cycle_credit: string;         // ACRCYCR
  curr_cycle_debit: string;          // ACRCYDB
  group_id: string | null;           // AADDGRP — ACCT-GROUP-ID X(10)
  updated_at: string;                // Used as optimistic_lock_version in PUT
  customer: CustomerDetailResponse;
}

/**
 * Customer update fields in account update request.
 * SSN split into 3 parts matching ACTSSN1/2/3 BMS fields.
 * Phone stored as NNN-NNN-NNNN combining ACSPH1A/B/C parts.
 */
export interface CustomerUpdateRequest {
  customer_id: number;
  first_name: string;          // ACSFNAM — alpha/hyphen/apostrophe only
  middle_name?: string;        // ACSMNAM
  last_name: string;           // ACSLNAM — alpha/hyphen/apostrophe only
  address_line_1?: string;
  address_line_2?: string;
  city?: string;
  state_code?: string;
  zip_code?: string;
  country_code?: string;
  phone_1?: string;            // NNN-NNN-NNNN format
  phone_2?: string;
  ssn_part1: string;           // ACTSSN1 — 3 digits; validated not 000/666/900-999
  ssn_part2: string;           // ACTSSN2 — 2 digits
  ssn_part3: string;           // ACTSSN3 — 4 digits
  date_of_birth: string;       // DOBYEAR/DOBMON/DOBDAY combined → YYYY-MM-DD
  fico_score?: number;         // ACSTFCO — 300-850
  government_id_ref?: string;
  eft_account_id?: string;
  primary_card_holder: 'Y' | 'N'; // ACSPFLG
}

/**
 * Account update request body.
 * All COACTUPC validation rules enforced by Zod schema.
 */
export interface AccountUpdateRequest {
  active_status: 'Y' | 'N';
  open_date: string;           // YYYY-MM-DD
  expiration_date: string;     // YYYY-MM-DD
  reissue_date: string;        // YYYY-MM-DD
  credit_limit: string;        // >= 0
  cash_credit_limit: string;   // >= 0 and <= credit_limit
  current_balance: string;
  curr_cycle_credit: string;
  curr_cycle_debit: string;
  group_id?: string;
  customer: CustomerUpdateRequest;
}

// ---------------------------------------------------------------------------
// Credit Card types — maps CARDDAT VSAM KSDS
// COBOL origin: COCRDLIC (list), COCRDSLC (view), COCRDUPC (update)
// BMS maps: CCRDLIA (list), CCRDSLA (view), CCRDUPA (update)
// ---------------------------------------------------------------------------

/**
 * Single row in card list response.
 * card_number_masked shows only last 4 digits per PCI-DSS.
 * COBOL: COCRDLIC CRDSELn, ACCTNOn, CRDNUMn, CRDSTSn row fields.
 */
export interface CardListItem {
  card_number: string;          // Full card number (for API calls)
  card_number_masked: string;   // CRDNUMn — ************XXXX for display
  account_id: number;           // ACCTNOn — ACCT-ID 9(11)
  active_status: string;        // CRDSTSn — Y/N
}

/**
 * Paginated card list response.
 * Original COCRDLIC showed 7 rows per page (CRDSTP1-7 markers).
 */
export interface CardListResponse {
  items: CardListItem[];
  page: number;
  page_size: number;
  total_count: number;
  has_next: boolean;
  has_previous: boolean;
}

/**
 * Card detail response — maps CCRDUPA BMS map display fields.
 * updated_at is used as optimistic_lock_version in PUT (replaces CCUP-OLD-DETAILS).
 */
export interface CardDetailResponse {
  card_number: string;              // CARDSID — CARD-NUM X(16)
  account_id: number;               // ACCTSID — PROT in COCRDUPC; cannot change
  card_embossed_name: string | null; // CRDNAME — alpha-only validated
  active_status: string;            // CRDSTCD — Y/N
  expiration_month: number;         // EXPMON — 1-12
  expiration_year: number;          // EXPYEAR — 1950-2099
  expiration_day: number | null;    // EXPDAY — DRK PROT FSET hidden field
  updated_at: string;               // optimistic_lock_version for PUT request
}

/**
 * Card update request body.
 * account_id NOT included — PROT in COCRDUPC (cannot be changed).
 * optimistic_lock_version = updated_at from GET (replaces CCUP-OLD-DETAILS snapshot).
 */
export interface CardUpdateRequest {
  card_embossed_name: string;       // CRDNAME — alpha-only
  active_status: 'Y' | 'N';        // CRDSTCD
  expiration_month: number;         // EXPMON — 1-12
  expiration_year: number;          // EXPYEAR — 1950-2099
  expiration_day?: number;          // EXPDAY — hidden state
  optimistic_lock_version: string;  // ISO datetime from GET response
}

/**
 * Query parameters for GET /api/v1/cards.
 */
export interface CardListParams {
  account_id?: number;
  card_number?: string;
  page?: number;
  page_size?: number;
}

// ---------------------------------------------------------------------------
// Auth store types
// ---------------------------------------------------------------------------

export interface AuthUser {
  user_id: string;
  user_type: UserType;
  first_name?: string;
  last_name?: string;
}

export interface AuthStore {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: AuthUser, token: string) => void;
  clearAuth: () => void;
}

// ---------------------------------------------------------------------------
// Transaction types — maps TRANSACT VSAM KSDS (CVTRA05Y / COTRN02Y copybooks)
// COBOL origin: COTRN00C (list), COTRN01C (view), COTRN02C (add)
// BMS maps: CTRN0A (list), CTRN1A (view), CTRN2A (add)
// ---------------------------------------------------------------------------

/**
 * Single row in transaction list.
 * COBOL origin: COTRN00C POPULATE-TRAN-DATA loop — 10 rows per page.
 * Maps CTRN0AO output fields: TNUMBn, TCARDn, TTYPEn, TCATn, TSOURn, TDESCn, TAMTn, TODATEn.
 */
export interface TransactionListItem {
  transaction_id: string;           // TRAN-ID X(16)
  card_number: string;              // TRAN-CARD-NUM X(16)
  transaction_type_code: string;    // TRAN-TYPE-CD X(02)
  transaction_category_code: string | null; // TRAN-CAT-CD 9(04)
  transaction_source: string | null; // TRAN-SOURCE X(10)
  description: string | null;       // TRAN-DESC
  amount: string;                   // TRAN-AMT S9(09)V99 — as string Decimal
  original_date: string | null;     // TRAN-ORIG-TS date portion
  processed_date: string | null;    // TRAN-PROC-TS date portion
}

/**
 * Transaction detail response from GET /api/v1/transactions/{transaction_id}.
 * COBOL origin: COTRN01C POPULATE-TRAN-FIELDS — all TRAN-RECORD fields displayed.
 */
export interface TransactionDetailResponse extends TransactionListItem {
  merchant_id: string | null;       // TRAN-MERCHANT-ID 9(09)
  merchant_name: string | null;     // TRAN-MERCHANT-NAME
  merchant_city: string | null;     // TRAN-MERCHANT-CITY
  merchant_zip: string | null;      // TRAN-MERCHANT-ZIP
  created_at: string | null;
  updated_at: string | null;
}

/**
 * Paginated transaction list response.
 * COBOL origin: COTRN00C paging state:
 *   has_next        → CDEMO-CT00-NEXT-PAGE-FLG='Y'
 *   has_previous    → page > 1
 *   first_item_key  → CDEMO-CT00-TRNID-FIRST
 *   last_item_key   → CDEMO-CT00-TRNID-LAST
 */
export interface TransactionListResponse {
  items: TransactionListItem[];
  page: number;
  page_size: number;
  total_count: number;
  has_next: boolean;
  has_previous: boolean;
  first_item_key: string | null;
  last_item_key: string | null;
}

/**
 * Request body for POST /api/v1/transactions.
 * COBOL origin: COTRN02C CTRN2AI input map fields.
 * Requires confirm='Y' — gating condition before ADD-TRANSACTION.
 * card_number XOR account_id (mutual exclusion from COTRN02C).
 */
export interface TransactionCreateRequest {
  card_number?: string;                   // CARDINPI — 16-char
  account_id?: number;                    // ACCTIDOI — 11-digit
  transaction_type_code: string;          // TRNTYPE — 2-digit
  transaction_category_code?: string;     // TRNCAT — 4-digit
  transaction_source?: string;            // TRNSRC — max 10
  description?: string;                   // TRNDESC
  amount: string;                         // TRNAMT — non-zero
  original_date: string;                  // TRNORIGDT — YYYY-MM-DD
  processed_date: string;                 // TRNPROCDT — >= original_date
  merchant_id?: string;                   // TRNMID — 9-digit
  merchant_name?: string;                 // TRNMNAME
  merchant_city?: string;                 // TRNMCITY
  merchant_zip?: string;                  // TRNMZIP
  confirm: 'Y';                           // CONFIRMI — must be 'Y'
}

/**
 * Query parameters for GET /api/v1/transactions.
 */
export interface TransactionListParams {
  page?: number;
  page_size?: number;
  tran_id_filter?: string;
  account_id?: number;
}

// ---------------------------------------------------------------------------
// Billing types — maps COBIL00C (CBIL0A BMS map)
// Two-phase: Phase 1 = GET balance, Phase 2 = POST payment
// ---------------------------------------------------------------------------

/**
 * Balance response from GET /api/v1/billing/{account_id}/balance.
 * COBOL origin: COBIL00C Phase 1 — READ-ACCTDAT-FILE → display ACCT-CURR-BAL as CURBAL.
 */
export interface BillingBalanceResponse {
  account_id: number;        // ACTIDINO on CBIL0A
  current_balance: string;   // CURBAL — ACCT-CURR-BAL (PICOUT format)
  credit_limit: string;      // CRLIMIT — ACCT-CREDIT-LIMIT
  available_credit: string;  // computed: credit_limit - current_balance
}

/**
 * Payment request body for POST /api/v1/billing/{account_id}/payment.
 * COBOL origin: COBIL00C CONFIRMI='Y' → CONF-PAY-YES path.
 */
export interface BillPaymentRequest {
  confirm: 'Y';  // CONFIRMI — must be 'Y' to execute payment
}

/**
 * Payment response.
 * COBOL origin: COBIL00C CONF-PAY-YES:
 *   previous_balance → original ACCT-CURR-BAL before COMPUTE
 *   new_balance      → 0.00 after COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT
 *   transaction_id   → generated via sequence (replaces STARTBR/READPREV race)
 */
export interface BillPaymentResponse {
  account_id: number;
  previous_balance: string;
  new_balance: string;        // Always '0.00' — COBIL00C clears full balance
  transaction_id: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Report types — maps CORPT00C (CRPT0A BMS map)
// COBOL origin: CORPT00C WRITEQ TD QUEUE='JOBS' → replaced by DB record + background task
// ---------------------------------------------------------------------------

/**
 * Report request body for POST /api/v1/reports/request.
 * COBOL origin: CORPT00C input map CRPT0AI.
 *   report_type: MONTHLYI='M', YEARLYI='Y', CUSTOMI='C'
 *   start_date/end_date: only for 'C' type
 *   confirm: CONFIRMI — must be 'Y'
 */
export interface ReportRequestCreate {
  report_type: 'M' | 'Y' | 'C';   // MONTHLYI/YEARLYI/CUSTOMI
  start_date?: string;              // SDTYYYY1I+SDTMMI+SDTDDI — YYYY-MM-DD
  end_date?: string;                // EDTYYYY1I+EDTMMI+EDTDDI — YYYY-MM-DD
  confirm: 'Y';                     // CONFIRMI
}

/**
 * Report request response from POST /api/v1/reports/request (202 Accepted).
 * COBOL origin: Replaces TDQ WRITEQ — returns request_id for status polling.
 */
export interface ReportRequestResponse {
  request_id: number;
  report_type: string;
  start_date: string | null;
  end_date: string | null;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  requested_at: string;
  message: string;
}

/**
 * Report status response from GET /api/v1/reports/{report_id}.
 * CORPT00C had no status tracking — this is a modern addition.
 */
export interface ReportStatusResponse {
  request_id: number;
  report_type: string;
  start_date: string | null;
  end_date: string | null;
  requested_by: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  result_path: string | null;
  error_message: string | null;
  requested_at: string;
  completed_at: string | null;
}
