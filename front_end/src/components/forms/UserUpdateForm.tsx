/**
 * UserUpdateForm — COUSR02C (CU02) Update User screen conversion.
 *
 * BMS Map: COUSR2A (COUSR02 mapset), 24x80
 *
 * Two-phase interaction (mirroring COUSR02C):
 *   Phase 1: User arrives (pre-populated from list selection or direct nav)
 *            → form shows current values from GET /api/users/{user_id}
 *   Phase 2: User edits fields, clicks Save (PF5) or Save & Exit (PF3)
 *
 * BMS field layout:
 *   Row 6:  Enter User ID (USRIDIN, IC) — search/lookup field
 *   Row 11: First Name (col 18, len 20)  Last Name (col 56, len 20)
 *   Row 13: Password (col 16, len 8, DRK)
 *   Row 15: User Type (col 17, len 1) hint "(A=Admin, U=User)"
 *   Row 23: ERRMSG
 *   Row 24: ENTER=Fetch  F3=Save&Exit  F4=Clear  F5=Save  F12=Cancel
 *
 * COUSR02C behaviour preserved:
 *   - User ID is ASKIP after fetch (read-only — not in REWRITE fields)
 *   - PF3 saves then exits to user list (save-and-exit)
 *   - PF5 saves and stays on screen
 *   - PF12 cancels without saving
 *   - No-change produces info message 'Please modify to update ...'
 */
'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/components/ui/Button';
import { FormField } from '@/components/ui/FormField';
import { StatusMessage } from '@/components/ui/StatusMessage';
import { ApiError, getUser, updateUser } from '@/lib/api';
import { getErrorMessage } from '@/lib/utils';
import type { UserResponse } from '@/types/user';

const schema = z.object({
  first_name: z
    .string()
    .min(1, 'First Name can NOT be empty...')
    .max(20, 'First Name must be at most 20 characters'),
  last_name: z
    .string()
    .min(1, 'Last Name can NOT be empty...')
    .max(20, 'Last Name must be at most 20 characters'),
  password: z.string().min(1, 'Password can NOT be empty...'),
  user_type: z.enum(['A', 'U'], {
    errorMap: () => ({ message: 'User Type must be A (Admin) or U (User)' }),
  }),
});

type FormValues = z.infer<typeof schema>;

interface UserUpdateFormProps {
  /** user_id pre-selected from list (CDEMO-CU02-USR-SELECTED in COBOL) */
  userId: string;
}

type MessageState = {
  text: string;
  type: 'success' | 'error' | 'info';
} | null;

export function UserUpdateForm({ userId }: UserUpdateFormProps) {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<MessageState>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  // On mount, auto-fetch user data (mirrors COUSR02C first-entry with pre-selected user)
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const data = await getUser(userId);
        setUser(data);
        reset({
          first_name: data.first_name,
          last_name: data.last_name,
          password: '',  // Password not pre-populated (DRK field in BMS)
          user_type: data.user_type,
        });
        // 'Press PF5 key to save your updates ...' (COUSR02C READ-USER-SEC-FILE success)
        setStatusMessage({
          text: 'Press Save (F5) to save your updates ...',
          type: 'info',
        });
      } catch (err) {
        if (err instanceof ApiError) {
          setLoadError(err.message);
        } else {
          setLoadError(getErrorMessage(err));
        }
      }
    };
    fetchUser();
  }, [userId, reset]);

  const doSave = async (data: FormValues): Promise<boolean> => {
    try {
      await updateUser(userId, data);
      setStatusMessage({
        text: `User ${userId} has been updated ...`,
        type: 'success',
      });
      return true;
    } catch (err) {
      if (err instanceof ApiError) {
        const type = err.status === 422 ? 'info' : 'error';
        setStatusMessage({ text: err.message, type });
      } else {
        setStatusMessage({ text: getErrorMessage(err), type: 'error' });
      }
      return false;
    }
  };

  // PF5 = Save (stay on screen)
  const handleSave = handleSubmit(async (data) => {
    await doSave(data);
  });

  // PF3 = Save & Exit → navigate back to user list
  const handleSaveAndExit = handleSubmit(async (data) => {
    const ok = await doSave(data);
    if (ok) {
      router.push('/users');
    }
  });

  // PF4 = Clear
  const handleClear = () => {
    reset({ first_name: '', last_name: '', password: '', user_type: 'U' });
    setStatusMessage(null);
  };

  // PF12 = Cancel (no save)
  const handleCancel = () => {
    router.push('/users');
  };

  if (loadError) {
    return (
      <StatusMessage
        message={`User ID NOT found: ${userId}`}
        type="error"
      />
    );
  }

  if (!user) {
    return <p className="text-gray-500 text-sm">Loading user data...</p>;
  }

  return (
    <div className="space-y-6">
      {/* User ID display — ASKIP (read-only, not in REWRITE) */}
      <div className="bg-gray-50 border border-gray-200 rounded-md px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-green-700">Enter User ID:</span>
          <span className="text-sm font-mono font-bold text-green-700">{userId}</span>
          <span className="text-xs text-gray-500 italic">
            (User ID is read-only — VSAM key cannot be changed)
          </span>
        </div>
      </div>

      {/* Separator — Row 8 asterisk line from BMS */}
      <div className="border-t-2 border-yellow-400" />

      {/* Status message */}
      {statusMessage && (
        <StatusMessage message={statusMessage.text} type={statusMessage.type} />
      )}

      <form noValidate>
        {/* Row 11: First Name + Last Name */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <FormField
            label="First Name"
            maxLength={20}
            error={errors.first_name?.message}
            {...register('first_name')}
          />
          <FormField
            label="Last Name"
            maxLength={20}
            error={errors.last_name?.message}
            {...register('last_name')}
          />
        </div>

        {/* Row 13: Password (DRK field — non-display in BMS) */}
        <div className="mb-4">
          <FormField
            label="Password"
            hint="(8 Char)"
            type="password"
            autoComplete="new-password"
            error={errors.password?.message}
            {...register('password')}
          />
        </div>

        {/* Row 15: User Type */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-cyan-700 mb-1">
            User Type
            <span className="ml-2 text-xs font-normal text-blue-600">(A=Admin, U=User)</span>
          </label>
          <select
            className={`rounded-md border px-3 py-2 text-sm w-full max-w-xs bg-white text-gray-900
              focus:outline-none focus:ring-2 focus:ring-blue-500
              ${errors.user_type ? 'border-red-500' : 'border-gray-300'}`}
            {...register('user_type')}
          >
            <option value="A">A - Admin</option>
            <option value="U">U - Regular User</option>
          </select>
          {errors.user_type && (
            <p className="text-xs text-red-600 mt-1">{errors.user_type.message}</p>
          )}
        </div>

        {/* Row 24: ENTER=Fetch F3=Save&Exit F4=Clear F5=Save F12=Cancel */}
        <div className="flex flex-wrap gap-3 pt-4 border-t border-gray-200">
          {/* F5=Save */}
          <Button type="button" onClick={handleSave} isLoading={isSubmitting}>
            Save (F5)
          </Button>
          {/* F3=Save & Exit */}
          <Button type="button" variant="secondary" onClick={handleSaveAndExit}>
            Save &amp; Exit (F3)
          </Button>
          {/* F4=Clear */}
          <Button type="button" variant="ghost" onClick={handleClear}>
            Clear (F4)
          </Button>
          {/* F12=Cancel */}
          <Button type="button" variant="ghost" onClick={handleCancel}>
            Cancel (F12)
          </Button>
        </div>
      </form>
    </div>
  );
}
