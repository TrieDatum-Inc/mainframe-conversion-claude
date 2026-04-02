'use client';

// ============================================================
// Add Card Page
// Mirrors COCRDUPC (card add/update program) — create path.
// ============================================================

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { cardsApi, getErrorMessage } from '@/lib/api';
import { cardCreateSchema, type CardCreateFormValues } from '@/lib/validators';
import { FormField, inputClass } from '@/components/ui/FormField';
import { PageHeader } from '@/components/ui/PageHeader';

export default function NewCardPage() {
  const router = useRouter();

  const { register, handleSubmit, formState: { errors } } = useForm<CardCreateFormValues>({
    resolver: zodResolver(cardCreateSchema),
  });

  const mutation = useMutation({
    mutationFn: (data: CardCreateFormValues) =>
      cardsApi.create(data as Record<string, unknown>),
    onSuccess: (response) => {
      const cardNum = response.data?.card_num;
      toast.success('Card created successfully');
      router.push(cardNum ? `/cards/${cardNum}` : '/cards');
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const fc = (key: keyof CardCreateFormValues) => inputClass(Boolean(errors[key]));

  return (
    <div>
      <PageHeader
        title="Add New Card"
        description="Create a new credit card for an account"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Cards', href: '/cards' },
          { label: 'New Card' },
        ]}
      />

      <div className="max-w-lg">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-5">
            <FormField label="Account ID" htmlFor="acct_id" error={errors.acct_id} required>
              <input
                id="acct_id"
                type="number"
                inputMode="numeric"
                min={1}
                {...register('acct_id', { valueAsNumber: true })}
                className={fc('acct_id')}
                placeholder="Enter account ID"
              />
            </FormField>

            <FormField label="Embossed Name" htmlFor="embossed_name" error={errors.embossed_name} required hint="Name printed on card (max 50 chars)">
              <input
                id="embossed_name"
                type="text"
                maxLength={50}
                {...register('embossed_name')}
                className={fc('embossed_name')}
                placeholder="JOHN DOE"
              />
            </FormField>

            <FormField label="Expiration Date" htmlFor="expiration_date" error={errors.expiration_date} required>
              <input
                id="expiration_date"
                type="text"
                maxLength={10}
                placeholder="YYYY-MM-DD"
                {...register('expiration_date')}
                className={fc('expiration_date')}
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
                Create Card
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
