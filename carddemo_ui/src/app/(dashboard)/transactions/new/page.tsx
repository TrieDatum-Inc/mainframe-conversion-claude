'use client';

// ============================================================
// Add Transaction Page
// Mirrors COTRN02C program and COTRN02 BMS map.
// Two input modes: by card_num or by acct_id.
// Fields match COTRN02 BMS map field definitions.
// ============================================================

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { transactionsApi, getErrorMessage } from '@/lib/api';
import { transactionCreateSchema, type TransactionCreateFormValues } from '@/lib/validators';
import { FormField, inputClass } from '@/components/ui/FormField';
import { PageHeader } from '@/components/ui/PageHeader';

type InputMode = 'card' | 'account';

export default function NewTransactionPage() {
  const router = useRouter();
  const [inputMode, setInputMode] = useState<InputMode>('card');

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<TransactionCreateFormValues>({
    resolver: zodResolver(transactionCreateSchema),
    defaultValues: { input_mode: 'card' },
  });

  const mutation = useMutation({
    mutationFn: (data: TransactionCreateFormValues) => {
      const payload: Record<string, unknown> = {
        tran_type_cd: data.tran_type_cd,
        tran_cat_cd: data.tran_cat_cd,
        tran_amt: data.tran_amt,
        merchant_id: data.merchant_id,
        merchant_name: data.merchant_name,
        merchant_city: data.merchant_city,
        merchant_zip: data.merchant_zip,
        tran_source: data.tran_source,
        tran_desc: data.tran_desc,
      };
      if (data.input_mode === 'card') {
        payload.card_num = data.card_num;
      } else {
        payload.acct_id = Number(data.acct_id);
      }
      return transactionsApi.create(payload);
    },
    onSuccess: (response) => {
      const tranId = response.data?.tran_id;
      toast.success('Transaction added successfully');
      router.push(tranId ? `/transactions/${tranId}` : '/transactions');
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const handleModeSwitch = (mode: InputMode) => {
    setInputMode(mode);
    setValue('input_mode', mode);
  };

  const fc = (key: keyof TransactionCreateFormValues) => inputClass(Boolean(errors[key]));

  return (
    <div>
      <PageHeader
        title="Add Transaction"
        description="Record a new transaction"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Transactions', href: '/transactions' },
          { label: 'New Transaction' },
        ]}
      />

      <div className="max-w-2xl">
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-6">
          {/* Input mode selector — COTRN02 supports both card_num and acct_id lookup */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <p className="text-sm font-semibold text-slate-700 mb-3">Transaction Source</p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleModeSwitch('card')}
                className={`flex-1 rounded-lg border py-2.5 text-sm font-medium transition-colors ${
                  inputMode === 'card'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                By Card Number
              </button>
              <button
                type="button"
                onClick={() => handleModeSwitch('account')}
                className={`flex-1 rounded-lg border py-2.5 text-sm font-medium transition-colors ${
                  inputMode === 'account'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                By Account ID
              </button>
            </div>

            <div className="mt-4">
              {inputMode === 'card' ? (
                <FormField label="Card Number" htmlFor="card_num" error={errors.card_num} required>
                  <input
                    id="card_num"
                    type="text"
                    maxLength={19}
                    placeholder="Enter card number"
                    {...register('card_num')}
                    className={fc('card_num')}
                  />
                </FormField>
              ) : (
                <FormField label="Account ID" htmlFor="acct_id" error={errors.acct_id} required>
                  <input
                    id="acct_id"
                    type="text"
                    inputMode="numeric"
                    placeholder="Enter account ID"
                    {...register('acct_id')}
                    className={fc('acct_id')}
                  />
                </FormField>
              )}
            </div>
          </div>

          {/* Transaction details */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <p className="text-sm font-semibold text-slate-700 mb-4">Transaction Details</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <FormField label="Transaction Type Code" htmlFor="tran_type_cd" error={errors.tran_type_cd} required hint="2-char code (e.g. SA, PY)">
                <input
                  id="tran_type_cd"
                  type="text"
                  maxLength={2}
                  {...register('tran_type_cd', { setValueAs: (v: string) => v.toUpperCase() })}
                  className={`${fc('tran_type_cd')} uppercase`}
                />
              </FormField>

              <FormField label="Category Code" htmlFor="tran_cat_cd" error={errors.tran_cat_cd} required>
                <input
                  id="tran_cat_cd"
                  type="text"
                  maxLength={4}
                  {...register('tran_cat_cd')}
                  className={fc('tran_cat_cd')}
                />
              </FormField>

              <FormField label="Amount" htmlFor="tran_amt" error={errors.tran_amt} required>
                <input
                  id="tran_amt"
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="0.00"
                  {...register('tran_amt', { valueAsNumber: true })}
                  className={fc('tran_amt')}
                />
              </FormField>

              <FormField label="Transaction Source" htmlFor="tran_source" error={errors.tran_source} required>
                <input
                  id="tran_source"
                  type="text"
                  maxLength={10}
                  {...register('tran_source')}
                  className={fc('tran_source')}
                />
              </FormField>

              <div className="sm:col-span-2">
                <FormField label="Description" htmlFor="tran_desc" error={errors.tran_desc} required>
                  <input
                    id="tran_desc"
                    type="text"
                    maxLength={100}
                    {...register('tran_desc')}
                    className={fc('tran_desc')}
                  />
                </FormField>
              </div>
            </div>
          </div>

          {/* Merchant details */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <p className="text-sm font-semibold text-slate-700 mb-4">Merchant Information</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <FormField label="Merchant ID" htmlFor="merchant_id" error={errors.merchant_id} required>
                <input
                  id="merchant_id"
                  type="text"
                  maxLength={9}
                  {...register('merchant_id')}
                  className={fc('merchant_id')}
                />
              </FormField>

              <FormField label="Merchant Name" htmlFor="merchant_name" error={errors.merchant_name} required>
                <input
                  id="merchant_name"
                  type="text"
                  maxLength={50}
                  {...register('merchant_name')}
                  className={fc('merchant_name')}
                />
              </FormField>

              <FormField label="City" htmlFor="merchant_city" error={errors.merchant_city} required>
                <input
                  id="merchant_city"
                  type="text"
                  maxLength={50}
                  {...register('merchant_city')}
                  className={fc('merchant_city')}
                />
              </FormField>

              <FormField label="ZIP Code" htmlFor="merchant_zip" error={errors.merchant_zip} required>
                <input
                  id="merchant_zip"
                  type="text"
                  maxLength={10}
                  {...register('merchant_zip')}
                  className={fc('merchant_zip')}
                />
              </FormField>
            </div>
          </div>

          <div className="flex justify-end gap-3">
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
              Add Transaction
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
