/**
 * Edit user page — derived from COUSR02C (CICS transaction CU02).
 * BMS map: COUSR02
 *
 * user_id cannot be changed (VSAM key).
 * Password update is optional.
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { FormField, Input, Select } from '@/components/ui/FormField';
import { Alert } from '@/components/ui/Alert';
import { userService } from '@/services/userService';
import { userUpdateSchema, type UserUpdateFormValues } from '@/lib/validators/user';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { UserResponse } from '@/lib/types/api';

interface PageProps {
  params: { id: string };
}

export default function EditUserPage({ params }: PageProps) {
  const userId = decodeURIComponent(params.id);
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<UserUpdateFormValues>({
    resolver: zodResolver(userUpdateSchema),
  });

  useEffect(() => {
    userService
      .getUser(userId)
      .then((data) => {
        setUser(data);
        reset({
          first_name: data.first_name ?? undefined,
          last_name: data.last_name ?? undefined,
          user_type: (data.user_type as 'A' | 'U') ?? undefined,
        });
      })
      .catch((err) => setLoadError(extractErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [userId, reset]);

  const onSubmit = async (values: UserUpdateFormValues) => {
    setIsSaving(true);
    setSaveError(null);
    try {
      await userService.updateUser(userId, values);
      setSaveSuccess(true);
      setTimeout(() => router.push(ROUTES.ADMIN_USERS), 1500);
    } catch (err) {
      setSaveError(extractErrorMessage(err));
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin h-8 w-8 rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Edit User</h1>
            <p className="page-subtitle">COUSR02C — {userId}</p>
          </div>
          <Link href={ROUTES.ADMIN_USERS}>
            <Button variant="outline" size="sm">Cancel</Button>
          </Link>
        </div>

        {loadError && <Alert variant="error" className="mb-4">{loadError}</Alert>}
        {saveError && <Alert variant="error" className="mb-4">{saveError}</Alert>}
        {saveSuccess && <Alert variant="success" className="mb-4">User updated successfully. Redirecting...</Alert>}

        {user && (
          <div className="card">
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 uppercase font-medium">User ID (read-only)</p>
              <p className="font-mono font-semibold text-gray-900 mt-1">{user.user_id}</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <FormField label="First Name" htmlFor="first_name" error={errors.first_name?.message}>
                  <Input id="first_name" maxLength={20} autoFocus {...register('first_name')} />
                </FormField>
                <FormField label="Last Name" htmlFor="last_name" error={errors.last_name?.message}>
                  <Input id="last_name" maxLength={20} {...register('last_name')} />
                </FormField>
              </div>

              <FormField label="User Type" htmlFor="user_type" error={errors.user_type?.message}>
                <Select id="user_type" {...register('user_type')}>
                  <option value="U">U — Regular User</option>
                  <option value="A">A — Administrator</option>
                </Select>
              </FormField>

              <FormField
                label="New Password (optional)"
                htmlFor="password"
                error={errors.password?.message}
                hint="Leave blank to keep current password"
              >
                <Input
                  id="password"
                  type="password"
                  maxLength={8}
                  hasError={!!errors.password}
                  {...register('password')}
                />
              </FormField>

              <div className="flex justify-end gap-3 pt-2">
                <Link href={ROUTES.ADMIN_USERS}>
                  <Button variant="outline">Cancel</Button>
                </Link>
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isSaving}
                  disabled={!isDirty}
                >
                  Save Changes
                </Button>
              </div>
            </form>
          </div>
        )}
      </div>
    </AppShell>
  );
}
