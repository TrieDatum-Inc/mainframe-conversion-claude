/**
 * New transaction page — derived from COTRN02C (CICS transaction CT02).
 * BMS map: COTRN02
 *
 * COBOL validation rules:
 *   - amount must not be zero
 *   - card_num: exactly 16 chars
 *   - type_cd: required
 *   - Validates card exists and is ACTIVE before writing
 */
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { FormField, Input, Select } from '@/components/ui/FormField';
import { Alert } from '@/components/ui/Alert';
import { transactionService } from '@/services/transactionService';
import { transactionCreateSchema, type TransactionCreateFormValues } from '@/lib/validators/transaction';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';

export default function NewTransactionPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TransactionCreateFormValues>({
    resolver: zodResolver(transactionCreateSchema),
    defaultValues: {
      source: 'POS TERM',
    },
  });

  const onSubmit = async (values: TransactionCreateFormValues) => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const txn = await transactionService.createTransaction(values);
      router.push(ROUTES.TRANSACTION_VIEW(txn.tran_id));
    } catch (err) {
      setSubmitError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">New Transaction</h1>
            <p className="page-subtitle">COTRN02C</p>
          </div>
          <Link href={ROUTES.TRANSACTIONS}>
            <Button variant="outline" size="sm">Cancel</Button>
          </Link>
        </div>

        <div className="card">
          {submitError && <Alert variant="error" className="mb-4">{submitError}</Alert>}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Required fields */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                label="Card Number"
                htmlFor="card_num"
                error={errors.card_num?.message}
                hint="TRAN-CARD-NUM PIC X(16) — 16 digits"
                required
              >
                <Input
                  id="card_num"
                  type="text"
                  inputMode="numeric"
                  maxLength={16}
                  autoFocus
                  placeholder="1234567890123456"
                  hasError={!!errors.card_num}
                  {...register('card_num')}
                />
              </FormField>

              <FormField
                label="Amount"
                htmlFor="amount"
                error={errors.amount?.message}
                hint="Must not be zero (COTRN02C validation)"
                required
              >
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500 text-sm">$</span>
                  <Input
                    id="amount"
                    type="text"
                    inputMode="decimal"
                    placeholder="0.00"
                    hasError={!!errors.amount}
                    className="pl-7"
                    {...register('amount')}
                  />
                </div>
              </FormField>

              <FormField
                label="Type Code"
                htmlFor="type_cd"
                error={errors.type_cd?.message}
                hint="TRAN-TYPE-CD PIC X(02)"
                required
              >
                <Select id="type_cd" hasError={!!errors.type_cd} {...register('type_cd')}>
                  <option value="">Select type...</option>
                  <option value="01">01 — Purchase</option>
                  <option value="02">02 — Bill Payment</option>
                  <option value="03">03 — Cash Advance</option>
                  <option value="04">04 — Refund</option>
                  <option value="05">05 — Fee</option>
                </Select>
              </FormField>

              <FormField label="Category Code" htmlFor="cat_cd" error={errors.cat_cd?.message}>
                <Input
                  id="cat_cd"
                  type="number"
                  min={0}
                  hasError={!!errors.cat_cd}
                  {...register('cat_cd', { valueAsNumber: true })}
                />
              </FormField>
            </div>

            {/* Optional fields */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Source" htmlFor="source" error={errors.source?.message}>
                <Input id="source" maxLength={10} {...register('source')} />
              </FormField>

              <FormField label="Description" htmlFor="description" error={errors.description?.message}>
                <Input id="description" maxLength={100} {...register('description')} />
              </FormField>

              <FormField label="Merchant Name" htmlFor="merchant_name" error={errors.merchant_name?.message}>
                <Input id="merchant_name" maxLength={50} {...register('merchant_name')} />
              </FormField>

              <FormField label="Merchant City" htmlFor="merchant_city" error={errors.merchant_city?.message}>
                <Input id="merchant_city" maxLength={50} {...register('merchant_city')} />
              </FormField>

              <FormField label="Merchant ZIP" htmlFor="merchant_zip" error={errors.merchant_zip?.message}>
                <Input id="merchant_zip" maxLength={10} {...register('merchant_zip')} />
              </FormField>

              <FormField label="Merchant ID" htmlFor="merchant_id" error={errors.merchant_id?.message}>
                <Input
                  id="merchant_id"
                  type="number"
                  min={0}
                  {...register('merchant_id', { valueAsNumber: true })}
                />
              </FormField>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Link href={ROUTES.TRANSACTIONS}>
                <Button variant="outline">Cancel</Button>
              </Link>
              <Button type="submit" variant="primary" isLoading={isSubmitting}>
                Create Transaction
              </Button>
            </div>
          </form>
        </div>
      </div>
    </AppShell>
  );
}
