/**
 * Card edit page — derived from COCRDUPC (CICS transaction CC0U).
 * BMS map: COCRDUP
 *
 * Updatable fields per COCRDUPC:
 *   - CARD-EMBOSSED-NAME PIC X(50)
 *   - CARD-ACTIVE-STATUS ('Y'/'N')
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
import { cardService } from '@/services/cardService';
import { cardUpdateSchema, type CardUpdateFormValues } from '@/lib/validators/card';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { CardResponse } from '@/lib/types/api';

interface PageProps {
  params: { cardNum: string };
}

export default function CardEditPage({ params }: PageProps) {
  const { cardNum } = params;
  const router = useRouter();
  const [card, setCard] = useState<CardResponse | null>(null);
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
  } = useForm<CardUpdateFormValues>({
    resolver: zodResolver(cardUpdateSchema),
  });

  useEffect(() => {
    cardService
      .getCard(cardNum)
      .then((data) => {
        setCard(data);
        reset({
          embossed_name: data.embossed_name ?? undefined,
          active_status: (data.active_status as 'Y' | 'N') ?? undefined,
        });
      })
      .catch((err) => setLoadError(extractErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [cardNum, reset]);

  const onSubmit = async (values: CardUpdateFormValues) => {
    setIsSaving(true);
    setSaveError(null);
    try {
      await cardService.updateCard(cardNum, values);
      setSaveSuccess(true);
      setTimeout(() => router.push(ROUTES.CARD_VIEW(cardNum)), 1500);
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
            <h1 className="page-title">Edit Card</h1>
            <p className="page-subtitle">COCRDUPC</p>
          </div>
          <Link href={ROUTES.CARD_VIEW(cardNum)}>
            <Button variant="outline" size="sm">Cancel</Button>
          </Link>
        </div>

        {loadError && <Alert variant="error" className="mb-4">{loadError}</Alert>}
        {saveError && <Alert variant="error" className="mb-4">{saveError}</Alert>}
        {saveSuccess && (
          <Alert variant="success" className="mb-4">Card updated successfully. Redirecting...</Alert>
        )}

        {card && (
          <div className="card">
            <p className="text-sm text-gray-500 mb-4 font-mono">{card.card_num}</p>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                label="Embossed Name"
                htmlFor="embossed_name"
                error={errors.embossed_name?.message}
                hint="CARD-EMBOSSED-NAME PIC X(50)"
              >
                <Input
                  id="embossed_name"
                  autoFocus
                  maxLength={50}
                  placeholder="Name on card"
                  hasError={!!errors.embossed_name}
                  {...register('embossed_name')}
                />
              </FormField>

              <FormField
                label="Active Status"
                htmlFor="active_status"
                error={errors.active_status?.message}
                hint="CARD-ACTIVE-STATUS PIC X(01)"
              >
                <Select id="active_status" hasError={!!errors.active_status} {...register('active_status')}>
                  <option value="">Select...</option>
                  <option value="Y">Y — Active</option>
                  <option value="N">N — Inactive</option>
                </Select>
              </FormField>

              <div className="flex justify-end gap-3 pt-2">
                <Link href={ROUTES.CARD_VIEW(cardNum)}>
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
