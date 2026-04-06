/**
 * Zod validation schemas for user management forms.
 *
 * COBOL origin: Replicates validation from COUSR01C and COUSR02C:
 *   FNAMEI blank  → 'First Name can NOT be empty...'
 *   LNAMEI blank  → 'Last Name can NOT be empty...'
 *   USERIDI blank → 'User ID can NOT be empty...'
 *   PASSWDI blank → 'Password can NOT be empty...'
 *   USRTYPEI not A/U → 'User Type can NOT be empty...'
 */

import { z } from 'zod';

/** Validation order mirrors COUSR01C EVALUATE TRUE short-circuit */
export const userCreateSchema = z.object({
  first_name: z
    .string()
    .min(1, 'First Name can NOT be empty')
    .max(20, 'First Name cannot exceed 20 characters')
    .refine((v) => v.trim().length > 0, 'First Name cannot be blank'),

  last_name: z
    .string()
    .min(1, 'Last Name can NOT be empty')
    .max(20, 'Last Name cannot exceed 20 characters')
    .refine((v) => v.trim().length > 0, 'Last Name cannot be blank'),

  user_id: z
    .string()
    .min(1, 'User ID can NOT be empty')
    .max(8, 'User ID cannot exceed 8 characters')
    .regex(/^[A-Za-z0-9]+$/, 'User ID must be alphanumeric only'),

  password: z
    .string()
    .min(1, 'Password can NOT be empty')
    .max(72, 'Password cannot exceed 72 characters'),

  user_type: z.enum(['A', 'U'], {
    errorMap: () => ({ message: 'User Type must be A (Admin) or U (User)' }),
  }),
});

export type UserCreateFormValues = z.infer<typeof userCreateSchema>;

/** COUSR02C: password optional on update */
export const userUpdateSchema = z.object({
  first_name: z
    .string()
    .min(1, 'First Name can NOT be empty')
    .max(20, 'First Name cannot exceed 20 characters')
    .refine((v) => v.trim().length > 0, 'First Name cannot be blank'),

  last_name: z
    .string()
    .min(1, 'Last Name can NOT be empty')
    .max(20, 'Last Name cannot exceed 20 characters')
    .refine((v) => v.trim().length > 0, 'Last Name cannot be blank'),

  password: z
    .string()
    .max(72, 'Password cannot exceed 72 characters')
    .optional()
    .or(z.literal('')),

  user_type: z.enum(['A', 'U'], {
    errorMap: () => ({ message: 'User Type must be A (Admin) or U (User)' }),
  }),
});

export type UserUpdateFormValues = z.infer<typeof userUpdateSchema>;
