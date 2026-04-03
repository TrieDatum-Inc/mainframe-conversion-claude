/**
 * UserAddForm — COUSR01C (CU01) Add User screen conversion.
 *
 * BMS Map: COUSR1A (COUSR01 mapset), 24x80
 *
 * Field layout from BMS spec:
 *   Row 8:  First Name (col 18, len 20)    Last Name (col 56, len 20)
 *   Row 11: User ID (col 15, len 8)        Password (col 55, len 8, DRK)
 *   Row 14: User Type (col 17, len 1) hint "(A=Admin, U=User)"
 *   Row 23: Error/status message (ERRMSG)
 *   Row 24: ENTER=Add User  F3=Back  F4=Clear
 *
 * Validations mirror COUSR01C PROCESS-ENTER-KEY:
 *   1. first_name required
 *   2. last_name required
 *   3. user_id required, max 8 chars
 *   4. password required
 *   5. user_type must be 'A' or 'U' (COBOL bug fix — original only checked NOT SPACES)
 */
'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/components/ui/Button';
import { FormField } from '@/components/ui/FormField';
import { StatusMessage } from '@/components/ui/StatusMessage';
import { ApiError, createUser } from '@/lib/api';
import { getErrorMessage } from '@/lib/utils';

// Zod schema mirrors COUSR01C PROCESS-ENTER-KEY validation order
const schema = z.object({
  first_name: z
    .string()
    .min(1, 'First Name can NOT be empty...')
    .max(20, 'First Name must be at most 20 characters'),
  last_name: z
    .string()
    .min(1, 'Last Name can NOT be empty...')
    .max(20, 'Last Name must be at most 20 characters'),
  user_id: z
    .string()
    .min(1, 'User ID can NOT be empty...')
    .max(8, 'User ID must be at most 8 characters (PIC X(08))')
    .regex(/^\S+$/, 'User ID must not contain spaces'),
  password: z
    .string()
    .min(1, 'Password can NOT be empty...'),
  user_type: z
    .enum(['A', 'U'], {
      errorMap: () => ({
        message: 'User Type must be A (Admin) or U (User)',
      }),
    }),
});

type FormValues = z.infer<typeof schema>;

interface UserAddFormProps {
  onSuccess?: () => void;
}

export function UserAddForm({ onSuccess }: UserAddFormProps) {
  const router = useRouter();
  const [statusMessage, setStatusMessage] = useState<{
    text: string;
    type: 'success' | 'error';
  } | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormValues) => {
    setStatusMessage(null);
    try {
      const created = await createUser(data);
      // COUSR01C WRITE-USER-SEC-FILE success: clear form, show green message
      // 'User [ID] has been added ...'
      setStatusMessage({
        text: `User ${created.user_id} has been added ...`,
        type: 'success',
      });
      reset();
      onSuccess?.();
    } catch (err) {
      if (err instanceof ApiError) {
        setStatusMessage({ text: err.message, type: 'error' });
      } else {
        setStatusMessage({ text: getErrorMessage(err), type: 'error' });
      }
    }
  };

  // PF4 = Clear — COUSR01C CLEAR-CURRENT-SCREEN / INITIALIZE-ALL-FIELDS
  const handleClear = () => {
    reset();
    setStatusMessage(null);
  };

  // PF3 = Back — COUSR01C DFHPF3 → COADM01C (admin menu)
  const handleBack = () => {
    router.push('/users');
  };

  return (
    <div className="space-y-6">
      {/* Status message — Row 23 ERRMSG field */}
      {statusMessage && (
        <StatusMessage message={statusMessage.text} type={statusMessage.type} />
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        {/* Row 8: First Name + Last Name side by side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <FormField
            label="First Name"
            placeholder="First Name"
            maxLength={20}
            autoFocus
            error={errors.first_name?.message}
            {...register('first_name')}
          />
          <FormField
            label="Last Name"
            placeholder="Last Name"
            maxLength={20}
            error={errors.last_name?.message}
            {...register('last_name')}
          />
        </div>

        {/* Row 11: User ID + Password side by side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <FormField
            label="User ID"
            hint="(8 Char)"
            placeholder="User ID"
            maxLength={8}
            error={errors.user_id?.message}
            {...register('user_id')}
          />
          <FormField
            label="Password"
            hint="(8 Char)"
            type="password"
            placeholder="Password"
            autoComplete="new-password"
            error={errors.password?.message}
            {...register('password')}
          />
        </div>

        {/* Row 14: User Type */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-cyan-700 mb-1">
            User Type
            <span className="ml-2 text-xs font-normal text-blue-600">(A=Admin, U=User)</span>
          </label>
          <select
            className={`rounded-md border px-3 py-2 text-sm w-full max-w-xs bg-white text-gray-900
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
              ${errors.user_type ? 'border-red-500' : 'border-gray-300 hover:border-gray-400'}`}
            aria-invalid={!!errors.user_type}
            aria-describedby={errors.user_type ? 'user_type-error' : undefined}
            {...register('user_type')}
          >
            <option value="">-- Select --</option>
            <option value="A">A - Admin</option>
            <option value="U">U - Regular User</option>
          </select>
          {errors.user_type && (
            <p id="user_type-error" className="text-xs text-red-600 mt-1" role="alert">
              {errors.user_type.message}
            </p>
          )}
        </div>

        {/* Row 24: Function key legend → action buttons */}
        <div className="flex flex-wrap gap-3 pt-4 border-t border-gray-200">
          {/* ENTER=Add User */}
          <Button type="submit" isLoading={isSubmitting}>
            Add User (Enter)
          </Button>
          {/* F3=Back */}
          <Button type="button" variant="secondary" onClick={handleBack}>
            Back (F3)
          </Button>
          {/* F4=Clear */}
          <Button type="button" variant="ghost" onClick={handleClear}>
            Clear (F4)
          </Button>
        </div>
      </form>
    </div>
  );
}
