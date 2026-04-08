/**
 * Account validators — derived from COACTUPC COBOL business rules.
 *
 * Source: app/cbl/COACTUPC.cbl
 * BMS map: COACTUP
 *
 * COBOL validation rules preserved:
 *   - active_status must be 'Y' or 'N'
 *   - credit_limit >= 0 (COMP-3)
 *   - ZIP code: 5-digit or 5+4 format (CSLKPCDY)
 *   - Monetary fields use Decimal precision (COMP-3 equivalent)
 */
import { z } from 'zod';

const decimalString = z
  .string()
  .regex(/^-?\d+(\.\d{1,2})?$/, 'Must be a valid decimal number')
  .optional();

const positiveDecimalString = z
  .string()
  .regex(/^\d+(\.\d{1,2})?$/, 'Must be a non-negative number')
  .refine((val) => parseFloat(val) >= 0, 'Must be greater than or equal to 0')
  .optional();

export const accountUpdateSchema = z.object({
  // ACCT-ACTIVE-STATUS PIC X(01): 'Y' or 'N'
  active_status: z.enum(['Y', 'N']).optional(),

  // ACCT-CURR-BAL PIC S9(10)V99 COMP-3
  curr_bal: decimalString,

  // ACCT-CREDIT-LIMIT PIC S9(10)V99 COMP-3 — must be >= 0
  credit_limit: positiveDecimalString,

  // ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99 COMP-3 — must be >= 0
  cash_credit_limit: positiveDecimalString,

  // ACCT-OPEN-DATE PIC X(10) YYYY-MM-DD
  open_date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format')
    .optional()
    .or(z.literal('')),

  // ACCT-EXPIRAION-DATE PIC X(10) YYYY-MM-DD
  expiration_date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format')
    .optional()
    .or(z.literal('')),

  // ACCT-REISSUE-DATE PIC X(10) YYYY-MM-DD
  reissue_date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format')
    .optional()
    .or(z.literal('')),

  // ACCT-CURR-CYC-CREDIT PIC S9(10)V99 COMP-3
  curr_cycle_credit: decimalString,

  // ACCT-CURR-CYC-DEBIT PIC S9(10)V99 COMP-3
  curr_cycle_debit: decimalString,

  // ACCT-ADDR-ZIP PIC X(10) — CSLKPCDY validation: XXXXX or XXXXX-XXXX
  addr_zip: z
    .string()
    .regex(/^\d{5}(-\d{4})?$/, 'ZIP code must be 5 digits (NNNNN) or ZIP+4 (NNNNN-NNNN)')
    .optional()
    .or(z.literal('')),

  // ACCT-GROUP-ID PIC X(10) — admin only
  group_id: z.string().max(10).optional(),
});

export const billPaymentSchema = z.object({
  // PYMTAMTI PIC X(09) — must be positive
  payment_amount: z
    .string()
    .min(1, 'Payment amount is required')
    .regex(/^\d+(\.\d{1,2})?$/, 'Payment amount must be a positive number')
    .refine((val) => parseFloat(val) > 0, 'Payment amount must be greater than zero'),

  description: z.string().max(100).optional(),
});

export type AccountUpdateFormValues = z.infer<typeof accountUpdateSchema>;
export type BillPaymentFormValues = z.infer<typeof billPaymentSchema>;
