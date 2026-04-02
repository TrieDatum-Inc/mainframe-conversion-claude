'use client';

// ============================================================
// Add Transaction Type Page (Admin Only)
// Mirrors COTRTUPC program — add path.
// Fields: tran_type_cd (PIC XX), tran_type_desc (PIC X(50)).
// ============================================================

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { transactionTypesApi, getErrorMessage } from '@/lib/api';
import { transactionTypeCreateSchema, type TransactionTypeCreateFormValues } from '@/lib/validators';
import { FormField, inputClass } from '@/components/ui/FormField';
import { PageHeader } from '@/components/ui/PageHeader';
import { useAuth } from '@/contexts/AuthContext';

export default function NewTransactionTypePage() {
  const { isAdmin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAdmin) router.replace('/transaction-types');
  }, [isAdmin, router]);

  const { register, handleSubmit, formState: { errors } } = useForm<TransactionTypeCreateFormValues>({
    resolver: zodResolver(transactionTypeCreateSchema),
  });

  const mutation = useMutation({
    mutationFn: (data: TransactionTypeCreateFormValues) =>
      transactionTypesApi.create(data as Record<string, unknown>),
    onSuccess: (_, variables) => {
      toast.success(`Transaction type ${variables.tran_type_cd} created`);
      router.push('/transaction-types');
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  if (!isAdmin) return null;

  const fc = (key: keyof TransactionTypeCreateFormValues) => inputClass(Boolean(errors[key]));

  return (
    <div>
      <PageHeader
        title="Add Transaction Type"
        description="Create a new transaction type code"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Transaction Types', href: '/transaction-types' },
          { label: 'New Type' },
        ]}
      />

      <div className="max-w-lg">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-5">
            <FormField
              label="Type Code"
              htmlFor="tran_type_cd"
              error={errors.tran_type_cd}
              required
              hint="Exactly 2 uppercase alphanumeric characters"
            >
              <input
                id="tran_type_cd"
                type="text"
                maxLength={2}
                autoFocus
                {...register('tran_type_cd', { setValueAs: (v: string) => v.toUpperCase() })}
                className={`${fc('tran_type_cd')} uppercase`}
                placeholder="SA"
              />
            </FormField>

            <FormField
              label="Description"
              htmlFor="tran_type_desc"
              error={errors.tran_type_desc}
              required
              hint="Maximum 50 characters"
            >
              <input
                id="tran_type_desc"
                type="text"
                maxLength={50}
                {...register('tran_type_desc')}
                className={fc('tran_type_desc')}
                placeholder="e.g. Sale Transaction"
              />
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
                Create Type
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
