'use client';

/**
 * Add User page — /admin/users/add
 *
 * COBOL origin: COUSR01C (Transaction CU01), BMS map COUSR1A
 *
 * Replaces:
 *   - Five-field entry form: FNAMEI, LNAMEI, USERIDI, PASSWDI, USRTYPEI
 *   - ENTER key → PROCESS-ENTER-KEY → WRITE-USER-SEC-FILE
 *   - PF3 → Back to Admin Menu (COADM01C)
 *   - PF4 → Clear all fields (INITIALIZE-ALL-FIELDS)
 *   - Success: fields cleared to allow adding another user (COUSR01C behavior after success)
 *   - Duplicate ID: 409 → 'User ID already exist...'
 *   - All five fields required (EVALUATE TRUE short-circuit order preserved)
 *
 * Admin only.
 */

import React, { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { createUser, extractError } from '@/lib/api';
import { userCreateSchema, UserCreateFormValues } from '@/lib/validations';
import { UserForm } from '@/components/forms/UserForm';
import { MessageBar } from '@/components/ui/MessageBar';

export default function AddUserPage() {
  const router = useRouter();
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UserCreateFormValues>({
    resolver: zodResolver(userCreateSchema),
    defaultValues: {
      user_id: '',
      first_name: '',
      last_name: '',
      password: '',
      user_type: undefined,
    },
  });

  /** ENTER handler → COUSR01C PROCESS-ENTER-KEY → POST /api/v1/users */
  const onSubmit = async (values: UserCreateFormValues) => {
    setSuccessMessage('');
    setErrorMessage('');

    try {
      const created = await createUser({
        user_id: values.user_id.toUpperCase(),
        first_name: values.first_name,
        last_name: values.last_name,
        password: values.password,
        user_type: values.user_type,
      });

      // COUSR01C INITIALIZE-ALL-FIELDS after success — reset form to allow adding another
      reset();
      setSuccessMessage(`User ${created.user_id} has been added successfully`);
    } catch (err) {
      const apiError = extractError(err);
      setErrorMessage(apiError.message);
    }
  };

  /** PF4 — Clear all fields (COUSR01C CLEAR-CURRENT-SCREEN) */
  const handleClear = () => {
    reset();
    setSuccessMessage('');
    setErrorMessage('');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-blue-900 text-white py-3 px-6">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-xs text-blue-300">COUSR01C | CU01</p>
            <h1 className="text-lg font-bold">Add New User</h1>
          </div>
          <div className="text-xs text-blue-300 text-right">
            <p>CardDemo Administration</p>
            <p>Admin Only</p>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {/* ERRMSGO — success (DFHGREEN) or error (DFHRED) */}
        {successMessage && <MessageBar message={successMessage} variant="success" />}
        {errorMessage && <MessageBar message={errorMessage} variant="error" />}

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <p className="text-sm text-gray-600 mb-4">
            Enter details for the new user. All fields are required.
          </p>

          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <UserForm
              mode="create"
              register={register}
              errors={errors}
              isSubmitting={isSubmitting}
            />

            {/* Action buttons */}
            <div className="flex gap-3 mt-6">
              {/* ENTER — primary submit */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? 'Adding...' : 'Add User'}
              </button>

              {/* PF4 — Clear */}
              <button
                type="button"
                onClick={handleClear}
                disabled={isSubmitting}
                className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded hover:bg-gray-200 disabled:opacity-50 transition-colors"
              >
                Clear (PF4)
              </button>
            </div>
          </form>
        </div>

        {/* PF3 — Back to Admin Menu */}
        <div className="flex gap-4">
          <Link
            href="/admin/users"
            className="text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 px-3 py-2 rounded transition-colors"
          >
            Back to User List
          </Link>
          <Link
            href="/admin/menu"
            className="text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 px-3 py-2 rounded transition-colors"
          >
            Admin Menu (PF3)
          </Link>
        </div>
      </main>
    </div>
  );
}
