/**
 * Transaction type create/edit page — derived from COTRTUPC (CICS transaction CTTU).
 * - /admin/transaction-types/new   → create new (TTUP-CREATE-NEW-RECORD)
 * - /admin/transaction-types/{cd}  → edit existing (only TR_DESCRIPTION updatable)
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { FormField, Input } from '@/components/ui/FormField';
import { Alert } from '@/components/ui/Alert';
import { transactionTypeService } from '@/services/transactionTypeService';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { TransactionTypeResponse } from '@/lib/types/api';

const editSchema = z.object({
  description: z
    .string()
    .min(1, 'Description cannot be blank (COTRTUPC 1230-EDIT-ALPHANUM-REQD)')
    .max(50, 'Description cannot exceed 50 characters (TR_DESCRIPTION CHAR(50))'),
});

const createSchema = z.object({
  type_cd: z
    .string()
    .regex(/^\d{1,2}$/, 'Type code must be 1-2 digit numeric (COTRTUPC 1245-EDIT-NUM-REQD)')
    .refine((v) => parseInt(v, 10) !== 0, 'Type code must not be zero'),
  description: z
    .string()
    .min(1, 'Description cannot be blank (COTRTUPC 1230-EDIT-ALPHANUM-REQD)')
    .max(50, 'Description cannot exceed 50 characters (TR_DESCRIPTION CHAR(50))'),
});

interface PageProps {
  params: { code: string };
}

export default function TransactionTypeEditPage({ params }: PageProps) {
  const code = decodeURIComponent(params.code);
  const isCreate = code === 'new';
  const router = useRouter();
  const [typeData, setTypeData] = useState<TransactionTypeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(!isCreate);
  const [isSaving, setIsSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<{ type_cd?: string; description: string }>({
    resolver: zodResolver(isCreate ? createSchema : editSchema),
    defaultValues: isCreate ? { type_cd: '', description: '' } : undefined,
  });

  useEffect(() => {
    if (isCreate) return;
    transactionTypeService
      .getTransactionType(code)
      .then((data) => {
        setTypeData(data);
        reset({ description: data.description });
      })
      .catch((err) => setLoadError(extractErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [code, isCreate, reset]);

  const onSubmit = async (values: { type_cd?: string; description: string }) => {
    setIsSaving(true);
    setSaveError(null);
    try {
      if (isCreate) {
        const padded = (values.type_cd ?? '').padStart(2, '0');
        await transactionTypeService.createTransactionType(padded, {
          description: values.description,
        });
      } else {
        await transactionTypeService.updateTransactionType(code, {
          description: values.description,
        });
      }
      setSaveSuccess(true);
      setTimeout(() => router.push(ROUTES.ADMIN_TRANSACTION_TYPES), 1500);
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
            <h1 className="page-title">{isCreate ? 'Add Transaction Type' : 'Edit Transaction Type'}</h1>
            <p className="page-subtitle">
              COTRTUPC {isCreate ? '— New record' : `— Type: ${code}`}
            </p>
          </div>
          <Link href={ROUTES.ADMIN_TRANSACTION_TYPES}>
            <Button variant="outline" size="sm">Cancel</Button>
          </Link>
        </div>

        {loadError && <Alert variant="error" className="mb-4">{loadError}</Alert>}
        {saveError && <Alert variant="error" className="mb-4">{saveError}</Alert>}
        {saveSuccess && (
          <Alert variant="success" className="mb-4">
            Transaction type {isCreate ? 'created' : 'updated'}. Redirecting...
          </Alert>
        )}

        {(isCreate || typeData) && (
          <div className="card">
            {!isCreate && typeData && (
              <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 uppercase font-medium">Type Code (read-only)</p>
                <p className="font-mono font-semibold text-gray-900 mt-1">{typeData.type_cd}</p>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {isCreate && (
                <FormField
                  label="Type Code"
                  htmlFor="type_cd"
                  error={errors.type_cd?.message}
                  hint="TR_TYPE CHAR(2) — 2-digit numeric, non-zero (COTRTUPC 1245-EDIT-NUM-REQD)"
                  required
                >
                  <Input
                    id="type_cd"
                    autoFocus
                    maxLength={2}
                    hasError={!!errors.type_cd}
                    {...register('type_cd')}
                  />
                </FormField>
              )}

              <FormField
                label="Description"
                htmlFor="description"
                error={errors.description?.message}
                hint="TR_DESCRIPTION CHAR(50) — COTRTUPC 1230-EDIT-ALPHANUM-REQD"
                required
              >
                <Input
                  id="description"
                  autoFocus={!isCreate}
                  maxLength={50}
                  hasError={!!errors.description}
                  {...register('description')}
                />
              </FormField>

              <div className="flex justify-end gap-3 pt-2">
                <Link href={ROUTES.ADMIN_TRANSACTION_TYPES}>
                  <Button variant="outline">Cancel</Button>
                </Link>
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isSaving}
                  disabled={!isCreate && !isDirty}
                >
                  {isCreate ? 'Create' : 'Save Changes'}
                </Button>
              </div>
            </form>
          </div>
        )}
      </div>
    </AppShell>
  );
}
