/**
 * Report validators — derived from CORPT00C COBOL business rules.
 *
 * Source: app/cbl/CORPT00C.cbl
 * BMS map: CORPT00 (CORPT0A)
 *
 * COBOL validation rules preserved:
 *   1. Report type must be 'monthly', 'yearly', or 'custom'
 *   2. For 'custom': start_date and end_date required
 *   3. Month: 1-12 (SDTMMI > '12' → error)
 *   4. Day: 1-31 (SDTDDI > '31' → error)
 *   5. start_date <= end_date
 */
import { z } from 'zod';

const dateString = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format')
  .refine((val) => {
    const [year, month, day] = val.split('-').map(Number);
    const m = month;
    const d = day;
    if (m < 1 || m > 12) return false; // CORPT00C: SDTMMI > '12' → error
    if (d < 1 || d > 31) return false; // CORPT00C: SDTDDI > '31' → error
    const date = new Date(year, m - 1, d);
    return date.getFullYear() === year && date.getMonth() === m - 1 && date.getDate() === d;
  }, 'Date must be a valid calendar date (CSUTLDTC validation)');

export const reportSubmitSchema = z
  .object({
    report_type: z.enum(['monthly', 'yearly', 'custom'], {
      errorMap: () => ({ message: 'Report type must be monthly, yearly, or custom' }),
    }),
    start_date: dateString.optional().or(z.literal('')),
    end_date: dateString.optional().or(z.literal('')),
  })
  .superRefine((data, ctx) => {
    // CORPT00C: custom type requires both dates
    if (data.report_type === 'custom') {
      if (!data.start_date) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Start date is required for custom report type',
          path: ['start_date'],
        });
      }
      if (!data.end_date) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'End date is required for custom report type',
          path: ['end_date'],
        });
      }
      // CORPT00C: start_date must be <= end_date
      if (data.start_date && data.end_date && data.start_date > data.end_date) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Start date must not be after end date',
          path: ['start_date'],
        });
      }
    }
  });

export type ReportFormValues = z.infer<typeof reportSubmitSchema>;
