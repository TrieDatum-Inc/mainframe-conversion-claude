'use client';

// ============================================================
// Add User Page (Admin Only)
// Mirrors COUSR01C program and COUSR01 BMS map.
// Fields: usr_id (PIC X(8)), password (PIC X(8)), first_name,
//         last_name (max 20 each), usr_type ('A'/'U').
// ============================================================

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { usersApi, getErrorMessage } from '@/lib/api';
import { userCreateSchema, type UserCreateFormValues } from '@/lib/validators';
import { FormField, inputClass } from '@/components/ui/FormField';
import { PageHeader } from '@/components/ui/PageHeader';
import { useAuth } from '@/contexts/AuthContext';

export default function NewUserPage() {
  const { isAdmin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAdmin) router.replace('/dashboard');
  }, [isAdmin, router]);

  const { register, handleSubmit, formState: { errors } } = useForm<UserCreateFormValues>({
    resolver: zodResolver(userCreateSchema),
    defaultValues: { usr_type: 'U' },
  });

  const mutation = useMutation({
    mutationFn: (data: UserCreateFormValues) =>
      usersApi.create(data as Record<string, unknown>),
    onSuccess: (_, variables) => {
      toast.success(`User ${variables.usr_id} created successfully`);
      router.push(`/users/${variables.usr_id}`);
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  if (!isAdmin) return null;

  const fc = (key: keyof UserCreateFormValues) => inputClass(Boolean(errors[key]));

  return (
    <div>
      <PageHeader
        title="Add User"
        description="Create a new system user"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Users', href: '/users' },
          { label: 'New User' },
        ]}
      />

      <div className="max-w-lg">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-5">
            <FormField label="User ID" htmlFor="usr_id" error={errors.usr_id} required hint="1-8 uppercase alphanumeric characters">
              <input
                id="usr_id"
                type="text"
                maxLength={8}
                autoFocus
                {...register('usr_id', { setValueAs: (v: string) => v.toUpperCase() })}
                className={`${fc('usr_id')} uppercase`}
                placeholder="e.g. JOHNDOE1"
              />
            </FormField>

            <FormField label="Password" htmlFor="usr_password" error={errors.password} required hint="1-8 characters">
              <input
                id="usr_password"
                type="password"
                maxLength={8}
                {...register('password')}
                className={fc('password')}
                placeholder="Enter password"
              />
            </FormField>

            <div className="grid grid-cols-2 gap-4">
              <FormField label="First Name" htmlFor="first_name" error={errors.first_name} required>
                <input
                  id="first_name"
                  type="text"
                  maxLength={20}
                  {...register('first_name')}
                  className={fc('first_name')}
                  placeholder="First name"
                />
              </FormField>
              <FormField label="Last Name" htmlFor="last_name" error={errors.last_name} required>
                <input
                  id="last_name"
                  type="text"
                  maxLength={20}
                  {...register('last_name')}
                  className={fc('last_name')}
                  placeholder="Last name"
                />
              </FormField>
            </div>

            <FormField label="User Type" htmlFor="usr_type" error={errors.usr_type} required>
              <select id="usr_type" {...register('usr_type')} className={fc('usr_type')}>
                <option value="U">User (U)</option>
                <option value="A">Administrator (A)</option>
              </select>
            </FormField>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => router.back()}
                className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={mutation.isPending}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-60"
              >
                {mutation.isPending && <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />}
                Create User
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
