'use client';

// ============================================================
// User Detail / Edit / Delete Page (Admin Only)
// Mirrors COUSR02C (update) + COUSR03C (delete) programs.
// ============================================================

import { use, useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Edit2, Trash2, Save, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { usersApi, getErrorMessage } from '@/lib/api';
import { userUpdateSchema, type UserUpdateFormValues } from '@/lib/validators';
import type { User } from '@/lib/types';
import { FormField, inputClass } from '@/components/ui/FormField';
import { PageHeader } from '@/components/ui/PageHeader';
import { Badge, userTypeBadge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { useAuth } from '@/contexts/AuthContext';

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="border-b border-slate-100 bg-slate-50 px-5 py-3">
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function ReadonlyField({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs font-medium text-slate-500">{label}</span>
      <span className="text-sm text-slate-900">{value ?? '—'}</span>
    </div>
  );
}

export default function UserDetailPage({ params }: { params: Promise<{ usrId: string }> }) {
  const { usrId } = use(params);
  const { isAdmin, user: currentUser } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (!isAdmin) router.replace('/dashboard');
  }, [isAdmin, router]);

  const { data: user, isLoading, error } = useQuery({
    queryKey: ['user', usrId],
    queryFn: async () => {
      const response = await usersApi.get(usrId);
      return response.data as User;
    },
    enabled: isAdmin,
  });

  const { register, handleSubmit, formState: { errors } } = useForm<UserUpdateFormValues>({
    resolver: zodResolver(userUpdateSchema),
    values: user
      ? { first_name: user.first_name, last_name: user.last_name, usr_type: user.usr_type, password: '' }
      : undefined,
  });

  const updateMutation = useMutation({
    mutationFn: (data: UserUpdateFormValues) => {
      const payload: Record<string, unknown> = {
        first_name: data.first_name,
        last_name: data.last_name,
        usr_type: data.usr_type,
      };
      if (data.password) payload.password = data.password;
      return usersApi.update(usrId, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', usrId] });
      toast.success('User updated successfully');
      setIsEditing(false);
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: () => usersApi.delete(usrId),
    onSuccess: () => {
      toast.success(`User ${usrId} deleted`);
      router.push('/users');
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  if (!isAdmin) return null;

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <LoadingSpinner size="lg" label="Loading user..." />
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="rounded-xl bg-red-50 border border-red-200 p-6 text-center">
        <p className="text-sm text-red-700 font-medium">
          {error ? getErrorMessage(error) : 'User not found'}
        </p>
        <button onClick={() => router.back()} className="mt-4 text-sm text-blue-600 hover:underline">Go back</button>
      </div>
    );
  }

  const isSelf = currentUser?.user_id === usrId;
  const fc = (key: keyof UserUpdateFormValues) => inputClass(Boolean(errors[key]));

  return (
    <div>
      <PageHeader
        title={`User: ${user.usr_id}`}
        description={`${user.first_name} ${user.last_name}`}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Users', href: '/users' },
          { label: user.usr_id },
        ]}
        actions={
          !isEditing ? (
            <div className="flex gap-2">
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Edit2 className="h-4 w-4" /> Edit
              </button>
              {!isSelf && (
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
                >
                  <Trash2 className="h-4 w-4" /> Delete
                </button>
              )}
            </div>
          ) : null
        }
      />

      <div className="max-w-lg">
        {isEditing ? (
          <form onSubmit={handleSubmit((d) => updateMutation.mutate(d))} className="space-y-6">
            <SectionCard title="Edit User">
              <div className="space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  <FormField label="First Name" htmlFor="first_name" error={errors.first_name} required>
                    <input id="first_name" type="text" maxLength={20} {...register('first_name')} className={fc('first_name')} />
                  </FormField>
                  <FormField label="Last Name" htmlFor="last_name" error={errors.last_name} required>
                    <input id="last_name" type="text" maxLength={20} {...register('last_name')} className={fc('last_name')} />
                  </FormField>
                </div>
                <FormField label="User Type" htmlFor="usr_type" error={errors.usr_type} required>
                  <select id="usr_type" {...register('usr_type')} className={fc('usr_type')} disabled={isSelf}>
                    <option value="U">User (U)</option>
                    <option value="A">Administrator (A)</option>
                  </select>
                  {isSelf && <p className="text-xs text-slate-400 mt-1">Cannot change your own user type</p>}
                </FormField>
                <FormField label="New Password" htmlFor="password" error={errors.password} hint="Leave blank to keep current password">
                  <input id="password" type="password" maxLength={8} {...register('password')} className={fc('password')} placeholder="New password (optional)" />
                </FormField>
              </div>
            </SectionCard>

            <div className="flex justify-end gap-3">
              <button type="button" onClick={() => setIsEditing(false)} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
                <X className="h-4 w-4" /> Cancel
              </button>
              <button type="submit" disabled={updateMutation.isPending} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-60">
                {updateMutation.isPending && <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />}
                <Save className="h-4 w-4" /> Save
              </button>
            </div>
          </form>
        ) : (
          <SectionCard title="User Information">
            <div className="grid grid-cols-2 gap-5">
              <ReadonlyField label="User ID" value={<span className="font-mono font-medium">{user.usr_id}</span>} />
              <ReadonlyField label="User Type" value={
                <Badge variant={userTypeBadge(user.usr_type)} label={user.usr_type === 'A' ? 'Administrator' : 'User'} />
              } />
              <ReadonlyField label="First Name" value={user.first_name} />
              <ReadonlyField label="Last Name" value={user.last_name} />
            </div>
          </SectionCard>
        )}
      </div>

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Delete User"
        message={`Are you sure you want to delete user ${user.usr_id} (${user.first_name} ${user.last_name})? This action cannot be undone.`}
        confirmLabel="Delete User"
        onConfirm={() => deleteMutation.mutate()}
        onCancel={() => setShowDeleteConfirm(false)}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
