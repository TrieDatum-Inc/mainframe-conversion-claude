'use client';

// ============================================================
// Card Detail / Edit Page
// Mirrors COCRDSLC (view) + COCRDUPC (update) programs.
// Fields: card_num, acct_id, embossed_name, expiration_date, active_status.
// ============================================================

import { use, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Edit2, X, Save } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';
import { cardsApi, getErrorMessage } from '@/lib/api';
import { cardUpdateSchema, type CardUpdateFormValues } from '@/lib/validators';
import type { Card } from '@/lib/types';
import { FormField, inputClass } from '@/components/ui/FormField';
import { PageHeader } from '@/components/ui/PageHeader';
import { Badge, statusBadge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

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

function EditForm({ card, onCancel, onSaved }: { card: Card; onCancel: () => void; onSaved: () => void }) {
  const queryClient = useQueryClient();

  const { register, handleSubmit, formState: { errors } } = useForm<CardUpdateFormValues>({
    resolver: zodResolver(cardUpdateSchema),
    defaultValues: {
      active_status: card.active_status,
      embossed_name: card.embossed_name ?? '',
      expiration_date: card.expiration_date ?? '',
    },
  });

  const mutation = useMutation({
    mutationFn: (data: CardUpdateFormValues) =>
      cardsApi.update(card.card_num, data as Record<string, unknown>),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['card', card.card_num] });
      toast.success('Card updated successfully');
      onSaved();
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const fc = (key: keyof CardUpdateFormValues) => inputClass(Boolean(errors[key]));

  return (
    <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-6">
      <SectionCard title="Card Details">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <FormField label="Active Status" htmlFor="active_status" error={errors.active_status}>
            <select id="active_status" {...register('active_status')} className={fc('active_status')}>
              <option value="Y">Active (Y)</option>
              <option value="N">Inactive (N)</option>
            </select>
          </FormField>
          <FormField label="Embossed Name" htmlFor="embossed_name" error={errors.embossed_name}>
            <input id="embossed_name" type="text" maxLength={50} {...register('embossed_name')} className={fc('embossed_name')} />
          </FormField>
          <FormField label="Expiration Date" htmlFor="expiration_date" error={errors.expiration_date} hint="YYYY-MM-DD">
            <input id="expiration_date" type="text" maxLength={10} placeholder="YYYY-MM-DD" {...register('expiration_date')} className={fc('expiration_date')} />
          </FormField>
        </div>
      </SectionCard>

      <div className="flex justify-end gap-3">
        <button type="button" onClick={onCancel} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
          <X className="h-4 w-4" /> Cancel
        </button>
        <button type="submit" disabled={mutation.isPending} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-60">
          {mutation.isPending && <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />}
          <Save className="h-4 w-4" /> Save Changes
        </button>
      </div>
    </form>
  );
}

export default function CardDetailPage({ params }: { params: Promise<{ cardNum: string }> }) {
  const { cardNum } = use(params);
  const [isEditing, setIsEditing] = useState(false);
  const router = useRouter();

  const { data: card, isLoading, error } = useQuery({
    queryKey: ['card', cardNum],
    queryFn: async () => {
      const response = await cardsApi.get(cardNum);
      return response.data as Card;
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <LoadingSpinner size="lg" label="Loading card..." />
      </div>
    );
  }

  if (error || !card) {
    return (
      <div className="rounded-xl bg-red-50 border border-red-200 p-6 text-center">
        <p className="text-sm text-red-700 font-medium">
          {error ? getErrorMessage(error) : 'Card not found'}
        </p>
        <button onClick={() => router.back()} className="mt-4 text-sm text-blue-600 hover:underline">Go back</button>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={`Card ****${card.card_num.slice(-4)}`}
        description={card.embossed_name ?? ''}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Cards', href: '/cards' },
          { label: `Card ${card.card_num.slice(-4)}` },
        ]}
        actions={
          <div className="flex gap-2">
            <Link
              href={`/accounts/${card.acct_id}`}
              className="px-3 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
            >
              View Account
            </Link>
            <Link
              href={`/transactions?card_num=${card.card_num}`}
              className="px-3 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Transactions
            </Link>
            {!isEditing && (
              <button onClick={() => setIsEditing(true)} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
                <Edit2 className="h-4 w-4" /> Edit
              </button>
            )}
          </div>
        }
      />

      {isEditing ? (
        <EditForm card={card} onCancel={() => setIsEditing(false)} onSaved={() => setIsEditing(false)} />
      ) : (
        <div className="max-w-xl">
          <SectionCard title="Card Information">
            <div className="grid grid-cols-2 gap-5">
              <ReadonlyField label="Card Number" value={<span className="font-mono text-xs">{card.card_num}</span>} />
              <ReadonlyField label="Account ID" value={
                <Link href={`/accounts/${card.acct_id}`} className="text-blue-600 hover:underline">
                  {card.acct_id}
                </Link>
              } />
              <ReadonlyField label="Embossed Name" value={card.embossed_name} />
              <ReadonlyField label="Expiration Date" value={card.expiration_date} />
              <ReadonlyField label="Status" value={
                <Badge variant={statusBadge(card.active_status)} label={card.active_status === 'Y' ? 'Active' : 'Inactive'} />
              } />
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  );
}
