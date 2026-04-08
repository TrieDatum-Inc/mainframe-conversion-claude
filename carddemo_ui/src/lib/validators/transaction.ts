/**
 * Transaction validators — derived from COTRN02C COBOL business rules.
 *
 * Source: app/cbl/COTRN02C.cbl
 * BMS map: COTRN02
 *
 * COBOL validation rules preserved:
 *   - amount must not be zero (COTRN02C validation)
 *   - card_num is required — 16 chars PIC X(16)
 *   - type_cd required PIC X(02)
 */
import { z } from 'zod';

export const transactionCreateSchema = z.object({
  // TRAN-AMT PIC S9(09)V99 COMP-3 — must not be zero
  amount: z
    .string()
    .min(1, 'Transaction amount is required')
    .regex(/^-?\d+(\.\d{1,2})?$/, 'Amount must be a valid decimal number')
    .refine((val) => parseFloat(val) !== 0, 'Transaction amount must not be zero'),

  // TRAN-CARD-NUM PIC X(16) — exactly 16 chars
  card_num: z
    .string()
    .length(16, 'Card number must be exactly 16 digits')
    .regex(/^\d{16}$/, 'Card number must contain only digits'),

  // TRAN-TYPE-CD PIC X(02) — required
  type_cd: z
    .string()
    .min(1, 'Transaction type is required')
    .max(2, 'Transaction type code cannot exceed 2 characters'),

  // Optional fields
  cat_cd: z.number().int().min(0).optional(),
  source: z.string().max(10).optional(),
  description: z.string().max(100).optional(),
  merchant_id: z.number().int().min(0).optional(),
  merchant_name: z.string().max(50).optional(),
  merchant_city: z.string().max(50).optional(),
  merchant_zip: z.string().max(10).optional(),
  orig_ts: z.string().max(26).optional(),
  proc_ts: z.string().max(26).optional(),
});

export type TransactionCreateFormValues = z.infer<typeof transactionCreateSchema>;
