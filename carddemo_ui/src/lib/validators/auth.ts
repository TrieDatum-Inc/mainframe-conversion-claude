/**
 * Authentication validators — derived from COSGN00C COBOL business rules.
 *
 * Source: app/cbl/COSGN00C.cbl
 * BMS map: COSGN00 (COSGN0A)
 *
 * COBOL validation rules preserved:
 *   - user_id must not be spaces/empty (WHEN USERIDI = SPACES)
 *   - password must not be spaces/empty (WHEN PASSWDI = SPACES)
 *   - user_id is uppercased before lookup (FUNCTION UPPER-CASE)
 *   - max 8 chars for both fields (PIC X(08))
 *   - whitespace-only is treated as blank (equivalent to SPACES check)
 */
import { z } from 'zod';

export const loginSchema = z.object({
  // USERIDI PIC X(08) — trim, uppercase, must not be spaces, max 8
  // Order: trim first (so leading/trailing spaces don't count toward max),
  // then uppercase, then validate non-empty and max length.
  user_id: z
    .string()
    .transform((val) => val.trim().toUpperCase())
    .pipe(
      z
        .string()
        .min(1, 'User ID cannot be blank')
        .max(8, 'User ID cannot exceed 8 characters')
    ),

  // PASSWDI PIC X(08) — must not be spaces
  password: z
    .string()
    .min(1, 'Password cannot be blank')
    .max(8, 'Password cannot exceed 8 characters'),
});

export type LoginFormValues = z.input<typeof loginSchema>;
export type LoginFormOutput = z.output<typeof loginSchema>;
