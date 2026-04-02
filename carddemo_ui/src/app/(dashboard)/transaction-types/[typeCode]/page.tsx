'use client';

// ============================================================
// Transaction Type Detail / Edit Page (Admin Only)
// Mirrors COTRTUPC update path.
// ============================================================

import { use, useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Edit2, Trash2, Save, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { transactionTypesApi, getErrorMessage } from '@/lib/api';
import { transactionTypeUpdateSchema, type TransactionTypeUpdateFormValues } from '@/lib/validators';
import type { TransactionType } from '@/lib/types';
import { FormField, inputClass } from '@/components/ui/FormField';
import { PageHeader } from '@/components/ui/PageHeader';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { useAuth } from '@/contexts/AuthContext';

export default function TransactionTypeDetailPage({ params }: { params: Promise<{ typeCode: string }> }) {
  const { typeCode } = use(params);
  const { isAdmin } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (!isAdmin) router.replace('/transaction-types');
  }, [isAdmin, router]);

  const { data: type, isLoading, error } = useQuery({
    queryKey: ['transaction-type', typeCode],
    queryFn: async () => {
      const response = await transactionTypesApi.get(typeCode);
      return response.data as TransactionType;
    },
    enabled: isAdmin,
  });

  const { register, handleSubmit, formState: { errors } } = useForm<TransactionTypeUpdateFormValues>({
    resolver: zodResolver(transactionTypeUpdateSchema),
    values: type ? { tran_type_desc: type.tran_type_desc } : undefined,
  });

  const updateMutation = useMutation({
    mutationFn: (data: TransactionTypeUpdateFormValues) =>
      transactionTypesApi.update(typeCode, data as Record<string, unknown>),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transaction-type', typeCode] });
      queryClient.invalidateQueries({ queryKey: ['transaction-types'] });
      toast.success('Transaction type updated');
      setIsEditing(false);
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: () => transactionTypesApi.delete(typeCode),
    onSuccess: () => {
      toast.success(`Transaction type ${typeCode} deleted`);
      router.push('/transaction-types');
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  if (!isAdmin) return null;

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <LoadingSpinner size="lg" label="Loading..." />
      </div>
    );
  }

  if (error || !type) {
    return (
      <div className="rounded-xl bg-red-50 border border-red-200 p-6 text-center">
        <p className="text-sm text-red-700">{error ? getErrorMessage(error) : 'Not found'}</p>
        <button onClick={() => router.back()} className="mt-4 text-sm text-blue-600 hover:underline">Go back</button>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={`Type: ${type.tran_type_cd}`}
        description={type.tran_type_desc}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Transaction Types', href: '/transaction-types' },
          { label: type.tran_type_cd },
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
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
              >
                <Trash2 className="h-4 w-4" /> Delete
              </button>
            </div>
          ) : null
        }
      />

      <div className="max-w-lg">
        {isEditing ? (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <form onSubmit={handleSubmit((d) => updateMutation.mutate(d))} className="space-y-5">
              <div>
                <span className="text-xs font-medium text-slate-500">Type Code (read-only)</span>
                <p className="mt-1 font-mono font-bold text-slate-900 text-lg">{type.tran_type_cd}</p>
              </div>
              <FormField label="Description" htmlFor="tran_type_desc" error={errors.tran_type_desc} required>
                <input
                  id="tran_type_desc"
                  type="text"
                  maxLength={50}
                  autoFocus
                  {...register('tran_type_desc')}
                  className={inputClass(Boolean(errors.tran_type_desc))}
                />
              </FormField>
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
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <div className="space-y-4">
              <div>
                <span className="text-xs font-medium text-slate-500">Type Code</span>
                <p className="mt-1 font-mono font-bold text-2xl text-slate-900">{type.tran_type_cd}</p>
              </div>
              <div>
                <span className="text-xs font-medium text-slate-500">Description</span>
                <p className="mt-1 text-base text-slate-800">{type.tran_type_desc}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Delete Transaction Type"
        message={`Are you sure you want to delete transaction type "${type.tran_type_cd}" (${type.tran_type_desc})?`}
        confirmLabel="Delete"
        onConfirm={() => deleteMutation.mutate()}
        onCancel={() => setShowDeleteConfirm(false)}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
