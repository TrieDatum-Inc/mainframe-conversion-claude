'use client';

/**
 * Edit User page — /admin/users/[userId]/edit
 *
 * COBOL origin: COUSR02C (Transaction CU02), BMS map COUSR2A
 *
 * Replaces:
 *   - READ-USER-SEC-FILE on first entry (auto-populate from CDEMO-CU02-USR-SELECTED)
 *   - UPDATE-USER-INFO: field-level change detection (WS-USR-MODIFIED flag)
 *   - PF5 → Save changes (UPDATE-USER-SEC-FILE)
 *   - PF3 → Back to User List (CDEMO-FROM-PROGRAM)
 *   - PF12 → Admin Menu without save (COADM01C)
 *   - 'Please modify to update...' (DFHRED) → 422 NoChangesDetectedError
 *   - Password not pre-filled (security) — leave blank to keep current
 *
 * Admin only.
 */

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { getUser, updateUser, extractError } from '@/lib/api';
import { userUpdateSchema, UserUpdateFormValues } from '@/lib/validations';
import { UserForm } from '@/components/forms/UserForm';
import { MessageBar } from '@/components/ui/MessageBar';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { UserResponse } from '@/types';

export default function EditUserPage() {
  const params = useParams();
  const userId = params.userId as string;
  const router = useRouter();

  const [currentUser, setCurrentUser] = useState<UserResponse | null>(null);
  const [loadError, setLoadError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [loading, setLoading] = useState(true);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UserUpdateFormValues>({
    resolver: zodResolver(userUpdateSchema),
  });

  /**
   * On mount: fetch current user data.
   * COUSR02C: first entry → PROCESS-ENTER-KEY (auto-lookup from CDEMO-CU02-USR-SELECTED)
   * → READ-USER-SEC-FILE → populate FNAMEI, LNAMEI, PASSWDI, USRTYPEI
   */
  useEffect(() => {
    const loadUser = async () => {
      setLoading(true);
      try {
        const user = await getUser(userId);
        setCurrentUser(user);
        // Pre-populate form (password intentionally NOT pre-filled — security)
        reset({
          first_name: user.first_name,
          last_name: user.last_name,
          password: '',
          user_type: user.user_type,
        });
      } catch (err) {
        const apiError = extractError(err);
        setLoadError(apiError.message);
      } finally {
        setLoading(false);
      }
    };
    loadUser();
  }, [userId, reset]);

  /**
   * PF5 → Save handler.
   * COUSR02C UPDATE-USER-INFO → UPDATE-USER-SEC-FILE (only if fields changed)
   */
  const onSubmit = async (values: UserUpdateFormValues) => {
    setSuccessMessage('');
    setErrorMessage('');

    try {
      const updated = await updateUser(userId, {
        first_name: values.first_name,
        last_name: values.last_name,
        password: values.password || undefined,
        user_type: values.user_type,
      });
      setCurrentUser(updated);
      // Clear password field after save
      reset({
        first_name: updated.first_name,
        last_name: updated.last_name,
        password: '',
        user_type: updated.user_type,
      });
      setSuccessMessage(`User ${updated.user_id} has been updated successfully`);
    } catch (err) {
      const apiError = extractError(err);
      // 422 NoChangesDetectedError → 'Please modify to update...' in DFHRED
      setErrorMessage(apiError.message);
    }
  };

  if (loading) return <LoadingSpinner label="Loading user..." />;
  if (loadError) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6">
        <MessageBar message={loadError} variant="error" />
        <Link href="/admin/users" className="text-blue-600 hover:underline text-sm mt-4 block">
          Back to User List
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-blue-900 text-white py-3 px-6">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-xs text-blue-300">COUSR02C | CU02</p>
            <h1 className="text-lg font-bold">Update User</h1>
          </div>
          <div className="text-xs text-blue-300">
            <p>User ID: {userId}</p>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {/* ERRMSGO: DFHGREEN on success, DFHRED on 'Please modify to update...' */}
        {successMessage && <MessageBar message={successMessage} variant="success" />}
        {errorMessage && <MessageBar message={errorMessage} variant="error" />}

        {/* Info prompt — DFHNEUTR 'Press PF5 key to save...' equivalent */}
        {!successMessage && !errorMessage && (
          <MessageBar message="Modify fields below and click Save to update." variant="info" />
        )}

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <UserForm
              mode="edit"
              userId={userId}
              register={register}
              errors={errors}
              isSubmitting={isSubmitting}
            />

            {/* Action buttons */}
            <div className="flex gap-3 mt-6">
              {/* PF5 — Save changes */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? 'Saving...' : 'Save Changes (PF5)'}
              </button>

              {/* PF3 — Back to User List (CDEMO-FROM-PROGRAM = COUSR00C) */}
              <Link
                href="/admin/users"
                className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded hover:bg-gray-200 transition-colors"
              >
                Back to Users (PF3)
              </Link>

              {/* PF12 — Cancel to Admin Menu without save */}
              <Link
                href="/admin/menu"
                className="px-4 py-2 text-gray-500 text-sm font-medium rounded hover:bg-gray-100 transition-colors"
              >
                Admin Menu (PF12)
              </Link>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
