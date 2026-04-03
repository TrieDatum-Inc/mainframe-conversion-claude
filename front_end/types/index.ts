/**
 * TypeScript type definitions for CardDemo Auth & Navigation module.
 *
 * Maps COBOL data structures:
 *   CARDDEMO-COMMAREA → AuthSession (stored in localStorage / context)
 *   COMEN02Y table entries → MenuOption
 *   COADM02Y table entries → MenuOption (admin)
 */

// ============================================================
// Authentication types — maps COSGN00C / CARDDEMO-COMMAREA
// ============================================================

/** Login form fields — maps COSGN0AI USERIDI and PASSWDI BMS fields */
export interface LoginFormData {
  /** COSGN0AI USERIDI PIC X(08) — max 8 chars, case-insensitive */
  user_id: string;
  /** COSGN0AI PASSWDI PIC X(08) — dark field on BMS screen */
  password: string;
}

/** User info from JWT token — maps CARDDEMO-COMMAREA fields */
export interface UserInfo {
  /** CDEMO-USER-ID PIC X(08) */
  user_id: string;
  first_name: string;
  last_name: string;
  /** CDEMO-USER-TYPE: 'A'=Admin, 'U'=Regular */
  user_type: "A" | "U";
}

/** Login API response — maps COSGN00C READ-USER-SEC-FILE success + XCTL */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
  /** Frontend route to navigate to after login (BR-006):
   *  '/admin-menu' for type='A', '/main-menu' for type='U' */
  redirect_to: string;
  server_time: string;
}

// ============================================================
// Menu types — maps COMEN02Y / COADM02Y table data
// ============================================================

/** Single menu option — maps CDEMO-MENU-OPTIONS OCCURS entry */
export interface MenuOption {
  /** CDEMO-MENU-OPT-NUM PIC 9(02) */
  option_number: number;
  /** CDEMO-MENU-OPT-NAME PIC X(35) */
  name: string;
  /** CDEMO-MENU-OPT-PGMNAME PIC X(08) */
  program_name: string;
  /** Modern frontend route */
  route: string;
  /** CDEMO-MENU-OPT-USRTYPE: 'U'=Regular 'A'=Admin */
  required_user_type: "U" | "A";
  /** False for DUMMY programs or uninstalled extensions */
  is_available: boolean;
  availability_message?: string | null;
}

/** Menu screen response — maps COMEN01C / COADM01C SEND-MENU-SCREEN */
export interface MenuResponse {
  menu_type: "main" | "admin";
  title: string;
  user: UserInfo;
  options: MenuOption[];
  server_time: string;
  /** TRNNAMEO — CM00 or CA00 */
  transaction_id: string;
  /** PGMNAMEO — COMEN01C or COADM01C */
  program_name: string;
}

/** Navigation result from option selection — maps PROCESS-ENTER-KEY XCTL */
export interface NavigateResponse {
  option_selected: number;
  program_name: string;
  route: string;
  message?: string | null;
  /** 'error' (RED DFHRED), 'info' (GREEN DFHGREEN), 'success' */
  message_type?: "error" | "info" | "success" | null;
}

// ============================================================
// Report types — maps CORPT00C / CORPT0A screen fields
// ============================================================

/** Report type selection — maps MONTHLYI / YEARLYI / CUSTOMI radio fields */
export type ReportType = "monthly" | "yearly" | "custom";

/** Report submission request — maps CORPT0AI fields */
export interface ReportSubmitRequest {
  /** Report type: monthly/yearly/custom (MONTHLYI/YEARLYI/CUSTOMI) */
  report_type: ReportType;
  /** SDTMM/SDTDD/SDTYYYY — custom start date (ISO format) */
  start_date?: string | null;
  /** EDTMM/EDTDD/EDTYYYY — custom end date (ISO format) */
  end_date?: string | null;
}

/** Report job response — maps post-submission success */
export interface ReportJobResponse {
  job_id: number;
  report_type: ReportType;
  start_date: string;
  end_date: string;
  status: "pending" | "running" | "completed" | "failed";
  submitted_by: string | null;
  submitted_at: string;
  message: string;
  message_type: "success" | "error" | "info";
}

/** Report jobs list response */
export interface ReportJobListResponse {
  jobs: ReportJobResponse[];
  total: number;
}

// ============================================================
// Payment types — maps COBIL00C / COBIL0A screen fields
// ============================================================

/** Account balance response — Phase 1 (COBIL00C READ-ACCTDAT-FILE) */
export interface AccountBalanceResponse {
  /** ACTIDINO — account ID displayed back to user */
  acct_id: string;
  /** CURBALI — current balance (ASKIP, protected display) */
  curr_bal: number;
  /** ERRMSG text if balance is zero */
  message: string | null;
  message_type: "error" | "info" | "success" | null;
}

/** Payment response — Phase 2 success (COBIL00C WRITE-TRANSACT-FILE success) */
export interface PaymentResponse {
  tran_id: string;
  acct_id: string;
  payment_amount: number;
  new_balance: number;
  orig_timestamp: string;
  /** 'Payment successful. Your Transaction ID is <TRAN-ID>.' */
  message: string;
  message_type: "success" | "error" | "info";
}

// ============================================================
// API error types
// ============================================================

export interface ApiError {
  detail: string | { message: string; message_type?: string };
}

export type MessageType = "error" | "info" | "success" | null;
