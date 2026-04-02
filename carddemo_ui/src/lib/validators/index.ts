// ============================================================
// CardDemo Zod Validation Schemas
// Business rules derived from COBOL field PIC clauses and
// backend validation logic.
// ============================================================

import { z } from 'zod';

// ---- Shared helpers ----

const US_STATE_CODES = new Set([
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN',
  'IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV',
  'NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN',
  'TX','UT','VT','VA','WA','WV','WI','WY','DC',
]);

const usStateCode = z
  .string()
  .length(2, 'State code must be 2 characters')
  .refine((val) => US_STATE_CODES.has(val.toUpperCase()), {
    message: 'Invalid US state code',
  });

/** Phone in format (999)999-9999 — matches COBOL COACTUP validation */
const phoneNumber = z
  .string()
  .regex(/^\(\d{3}\)\d{3}-\d{4}$/, 'Phone must be in format (999)999-9999');

/** FICO score 300–850 per COACTUP validation */
const ficoScore = z
  .number({ error: 'FICO score must be a number' })
  .int({ error: 'FICO score must be a whole number' })
  .min(300, { error: 'FICO score must be at least 300' })
  .max(850, { error: 'FICO score cannot exceed 850' });

/** Currency amount — positive decimal */
const currencyAmount = z
  .number({ error: 'Amount must be a number' })
  .nonnegative({ error: 'Amount must be zero or greater' })
  .multipleOf(0.01, { error: 'Amount must have at most 2 decimal places' });

/** Date string YYYY-MM-DD */
const dateString = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format');

// ---- Auth ----

export const loginSchema = z.object({
  user_id: z.string().min(1, 'User ID is required').max(8, 'User ID max 8 characters'),
  password: z.string().min(1, 'Password is required').max(8, 'Password max 8 characters'),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

// ---- Account Update ----

export const accountUpdateSchema = z.object({
  acct_active_status: z.string().max(1).optional(),
  acct_credit_limit: currencyAmount.optional(),
  acct_cash_credit_limit: currencyAmount.optional(),
  acct_open_date: dateString.optional(),
  acct_expiraion_date: dateString.optional(),
  acct_reissue_date: dateString.optional(),
  acct_group_id: z.string().max(10).optional(),
  cust_first_name: z.string().min(1, 'First name is required').max(25),
  cust_middle_name: z.string().max(25).optional(),
  cust_last_name: z.string().min(1, 'Last name is required').max(25),
  cust_addr_line_1: z.string().max(50).optional(),
  cust_addr_line_2: z.string().max(50).optional(),
  cust_addr_line_3: z.string().max(50).optional(),
  cust_addr_state_cd: usStateCode.optional(),
  cust_addr_country_cd: z.string().max(3).optional(),
  cust_addr_zip: z.string().max(10).optional(),
  cust_phone_num_1: phoneNumber.optional().or(z.literal('')),
  cust_phone_num_2: phoneNumber.optional().or(z.literal('')),
  cust_ssn: z.string().max(9).optional(),
  cust_govt_issued_id: z.string().max(20).optional(),
  cust_dob_yyyy_mm_dd: dateString.optional(),
  cust_fico_credit_score: ficoScore.optional(),
  cust_email_addr: z.string().email('Invalid email address').max(50).optional().or(z.literal('')),
  cust_pvt_ind: z.string().max(1).optional(),
  cust_ef_status: z.string().max(1).optional(),
});

export type AccountUpdateFormValues = z.infer<typeof accountUpdateSchema>;

// ---- Card Update ----

export const cardUpdateSchema = z.object({
  active_status: z.string().max(1).optional(),
  embossed_name: z.string().max(50).optional(),
  expiration_date: z.string().optional(),
});

export type CardUpdateFormValues = z.infer<typeof cardUpdateSchema>;

// ---- Card Create ----

export const cardCreateSchema = z.object({
  acct_id: z
    .number({ error: 'Account ID must be a number' })
    .int()
    .positive({ error: 'Account ID must be positive' }),
  embossed_name: z.string().min(1, 'Embossed name is required').max(50),
  expiration_date: z.string().min(1, 'Expiration date is required'),
});

export type CardCreateFormValues = z.infer<typeof cardCreateSchema>;

// ---- Transaction Create ----

export const transactionCreateSchema = z
  .object({
    tran_type_cd: z.string().min(1, 'Transaction type is required').max(2),
    tran_cat_cd: z.string().min(1, 'Category code is required').max(4),
    tran_amt: currencyAmount.refine((v) => v > 0, 'Amount must be greater than 0'),
    merchant_id: z.string().min(1, 'Merchant ID is required').max(9),
    merchant_name: z.string().min(1, 'Merchant name is required').max(50),
    merchant_city: z.string().min(1, 'Merchant city is required').max(50),
    merchant_zip: z.string().min(1, 'Merchant ZIP is required').max(10),
    tran_source: z.string().min(1, 'Source is required').max(10),
    tran_desc: z.string().min(1, 'Description is required').max(100),
    input_mode: z.enum(['card', 'account']),
    card_num: z.string().optional(),
    acct_id: z.union([z.number(), z.string()]).optional(),
  })
  .superRefine((data, ctx) => {
    if (data.input_mode === 'card' && !data.card_num) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Card number is required',
        path: ['card_num'],
      });
    }
    if (data.input_mode === 'account' && !data.acct_id) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Account ID is required',
        path: ['acct_id'],
      });
    }
  });

export type TransactionCreateFormValues = z.infer<typeof transactionCreateSchema>;

// ---- Reports ----

export const reportSchema = z
  .object({
    start_date: dateString,
    end_date: dateString,
    acct_id_filter: z.string().optional(),
  })
  .refine(
    (data) => new Date(data.end_date) >= new Date(data.start_date),
    { message: 'End date must be on or after start date', path: ['end_date'] },
  );

export type ReportFormValues = z.infer<typeof reportSchema>;

// ---- User Create ----

export const userCreateSchema = z.object({
  usr_id: z
    .string()
    .min(1, 'User ID is required')
    .max(8, 'User ID max 8 characters')
    .regex(/^[A-Z0-9]+$/, 'User ID must be uppercase alphanumeric'),
  password: z
    .string()
    .min(1, 'Password is required')
    .max(8, 'Password max 8 characters'),
  first_name: z.string().min(1, 'First name is required').max(20),
  last_name: z.string().min(1, 'Last name is required').max(20),
  usr_type: z.enum(['A', 'U'], { message: 'User type must be A or U' }),
});

export type UserCreateFormValues = z.infer<typeof userCreateSchema>;

// ---- User Update ----

export const userUpdateSchema = z.object({
  password: z.string().max(8).optional().or(z.literal('')),
  first_name: z.string().min(1, 'First name is required').max(20),
  last_name: z.string().min(1, 'Last name is required').max(20),
  usr_type: z.enum(['A', 'U'], { message: 'User type must be A or U' }),
});

export type UserUpdateFormValues = z.infer<typeof userUpdateSchema>;

// ---- Transaction Type Create ----

export const transactionTypeCreateSchema = z.object({
  tran_type_cd: z
    .string()
    .length(2, 'Type code must be exactly 2 characters')
    .regex(/^[A-Z0-9]+$/, 'Type code must be uppercase alphanumeric'),
  tran_type_desc: z.string().min(1, 'Description is required').max(50),
});

export type TransactionTypeCreateFormValues = z.infer<typeof transactionTypeCreateSchema>;

// ---- Transaction Type Update ----

export const transactionTypeUpdateSchema = z.object({
  tran_type_desc: z.string().min(1, 'Description is required').max(50),
});

export type TransactionTypeUpdateFormValues = z.infer<typeof transactionTypeUpdateSchema>;

// ---- Authorization Process ----

export const authProcessSchema = z.object({
  card_num: z.string().min(1, 'Card number is required').max(19),
  requested_amt: currencyAmount.refine((v) => v > 0, 'Amount must be greater than 0'),
  merchant_id: z.string().max(9).optional(),
  merchant_name: z.string().max(50).optional(),
});

export type AuthProcessFormValues = z.infer<typeof authProcessSchema>;

