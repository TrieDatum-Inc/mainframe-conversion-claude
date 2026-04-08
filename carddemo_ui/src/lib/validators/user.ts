/**
 * User management validators — derived from COUSR01C/COUSR02C COBOL business rules.
 *
 * Source: app/cbl/COUSR01C.cbl, COUSR02C.cbl
 * BMS maps: COUSR01, COUSR02
 *
 * COBOL validation rules preserved:
 *   - user_id: 8 chars max, uppercased, space-padded in COBOL
 *   - password: 8 chars max PIC X(08)
 *   - user_type: 'A' (admin) or 'U' (regular)
 *   - Duplicate user_id → DuplicateRecordError (CICS DUPREC → HTTP 409)
 */
import { z } from 'zod';

export const userCreateSchema = z.object({
  // SEC-USR-ID PIC X(08) — uppercased, space-padded
  user_id: z
    .string()
    .min(1, 'User ID cannot be blank')
    .max(8, 'User ID cannot exceed 8 characters')
    .transform((val) => val.toUpperCase()),

  // SEC-USR-PWD PIC X(08)
  password: z
    .string()
    .min(1, 'Password cannot be blank')
    .max(8, 'Password cannot exceed 8 characters'),

  // SEC-USR-FNAME PIC X(20)
  first_name: z.string().max(20, 'First name cannot exceed 20 characters').optional(),

  // SEC-USR-LNAME PIC X(20)
  last_name: z.string().max(20, 'Last name cannot exceed 20 characters').optional(),

  // SEC-USR-TYPE PIC X(01): 'A'=admin, 'U'=regular
  user_type: z.enum(['A', 'U'], {
    errorMap: () => ({ message: "User type must be 'A' (admin) or 'U' (regular)" }),
  }).default('U'),
});

export const userUpdateSchema = z.object({
  // SEC-USR-FNAME PIC X(20)
  first_name: z.string().max(20, 'First name cannot exceed 20 characters').optional(),

  // SEC-USR-LNAME PIC X(20)
  last_name: z.string().max(20, 'Last name cannot exceed 20 characters').optional(),

  // SEC-USR-TYPE PIC X(01)
  user_type: z.enum(['A', 'U']).optional(),

  // New password (optional update) — bcrypt hashed before storage
  password: z
    .string()
    .min(1, 'Password cannot be blank')
    .max(8, 'Password cannot exceed 8 characters')
    .optional(),
});

export type UserCreateFormValues = z.input<typeof userCreateSchema>;
export type UserCreateOutput = z.output<typeof userCreateSchema>;
export type UserUpdateFormValues = z.infer<typeof userUpdateSchema>;
