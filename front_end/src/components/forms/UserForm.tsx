'use client';

/**
 * UserForm — reusable form component for add and edit user screens.
 *
 * COBOL origin: Shared field layout from COUSR1A (add) and COUSR2A (update) maps:
 *   FNAMEI   → first_name input (UNPROT, max 20)
 *   LNAMEI   → last_name input (UNPROT, max 20)
 *   USERIDI  → user_id input (UNPROT, max 8; hidden on edit — key not changeable)
 *   PASSWDI  → password input (DRK → type="password"; required on create, optional on edit)
 *   USRTYPEI → user_type select ('A'=Admin, 'U'=User)
 *
 * Tab order preserved from BMS map definition:
 *   first_name → last_name → user_id → password → user_type
 *
 * COUSR02C note: User ID is not editable after lookup (USRIDINI is the lookup key).
 * On edit mode, user_id is displayed read-only.
 */

import React from 'react';
import { UseFormRegister, FieldErrors } from 'react-hook-form';
import type { UserCreateFormValues } from '@/lib/validations';
import type { UserUpdateFormValues } from '@/lib/validations';

interface UserFormProps {
  mode: 'create' | 'edit';
  userId?: string;       // Read-only user_id on edit screen
  register: UseFormRegister<UserCreateFormValues> | UseFormRegister<UserUpdateFormValues>;
  errors: FieldErrors<UserCreateFormValues> | FieldErrors<UserUpdateFormValues>;
  isSubmitting: boolean;
}

export function UserForm({ mode, userId, register, errors, isSubmitting }: UserFormProps) {
  const createReg = register as UseFormRegister<UserCreateFormValues>;
  const updateReg = register as UseFormRegister<UserUpdateFormValues>;

  return (
    <div className="space-y-4">
      {/* User ID — editable on create, read-only on edit */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          User ID
          <span className="text-red-500 ml-1">*</span>
        </label>
        {mode === 'create' ? (
          <>
            <input
              type="text"
              maxLength={8}
              placeholder="1-8 alphanumeric characters"
              autoFocus
              disabled={isSubmitting}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 uppercase"
              {...createReg('user_id')}
            />
            {(errors as FieldErrors<UserCreateFormValues>).user_id && (
              <p className="text-red-600 text-xs mt-1">
                {(errors as FieldErrors<UserCreateFormValues>).user_id?.message}
              </p>
            )}
          </>
        ) : (
          <div className="w-full border border-gray-200 rounded px-3 py-2 text-sm bg-gray-50 text-gray-500">
            {userId}
            <span className="ml-2 text-xs text-gray-400">(cannot be changed)</span>
          </div>
        )}
      </div>

      {/* First Name — FNAMEI (UNPROT, required) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          First Name
          <span className="text-red-500 ml-1">*</span>
        </label>
        <input
          type="text"
          maxLength={20}
          disabled={isSubmitting}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          {...(mode === 'create' ? createReg('first_name') : updateReg('first_name'))}
        />
        {errors.first_name && (
          <p className="text-red-600 text-xs mt-1">{errors.first_name.message}</p>
        )}
      </div>

      {/* Last Name — LNAMEI (UNPROT, required) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Last Name
          <span className="text-red-500 ml-1">*</span>
        </label>
        <input
          type="text"
          maxLength={20}
          disabled={isSubmitting}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          {...(mode === 'create' ? createReg('last_name') : updateReg('last_name'))}
        />
        {errors.last_name && (
          <p className="text-red-600 text-xs mt-1">{errors.last_name.message}</p>
        )}
      </div>

      {/* Password — PASSWDI (DRK → type=password) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Password
          {mode === 'create' && <span className="text-red-500 ml-1">*</span>}
          {mode === 'edit' && (
            <span className="text-gray-400 text-xs ml-2">(leave blank to keep current)</span>
          )}
        </label>
        <input
          type="password"
          maxLength={72}
          placeholder={mode === 'edit' ? 'Enter new password or leave blank' : ''}
          disabled={isSubmitting}
          autoComplete="new-password"
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          {...(mode === 'create' ? createReg('password') : updateReg('password'))}
        />
        {(errors as FieldErrors<UserCreateFormValues>).password && (
          <p className="text-red-600 text-xs mt-1">
            {(errors as FieldErrors<UserCreateFormValues>).password?.message}
          </p>
        )}
      </div>

      {/* User Type — USRTYPEI ('A'=Admin, 'U'=User) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          User Type
          <span className="text-red-500 ml-1">*</span>
        </label>
        <select
          disabled={isSubmitting}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          {...(mode === 'create' ? createReg('user_type') : updateReg('user_type'))}
        >
          <option value="">Select user type...</option>
          <option value="U">U - Regular User</option>
          <option value="A">A - Administrator</option>
        </select>
        {errors.user_type && (
          <p className="text-red-600 text-xs mt-1">{errors.user_type.message}</p>
        )}
      </div>
    </div>
  );
}
