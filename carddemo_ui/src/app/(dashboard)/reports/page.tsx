'use client';

// ============================================================
// Reports Page
// Mirrors CORPT00C program and CORPT00 BMS map.
// Fields: start_date (PIC X(10)), end_date (PIC X(10)), acct_id_filter (optional).
// PF5 = Generate Report (ENTER key equivalent).
// ============================================================

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { BarChart3, FileText } from 'lucide-react';
import { reportsApi, getErrorMessage } from '@/lib/api';
import { reportSchema, type ReportFormValues } from '@/lib/validators';
import type { ReportGenerateResponse } from '@/lib/types';
import { FormField, inputClass } from '@/components/ui/FormField';
import { PageHeader } from '@/components/ui/PageHeader';

export default function ReportsPage() {
  const [lastReport, setLastReport] = useState<ReportGenerateResponse | null>(null);

  const { register, handleSubmit, formState: { errors } } = useForm<ReportFormValues>({
    resolver: zodResolver(reportSchema),
    defaultValues: {
      start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
      end_date: new Date().toISOString().slice(0, 10),
    },
  });

  const mutation = useMutation({
    mutationFn: (data: ReportFormValues) => {
      const payload: Record<string, unknown> = {
        start_date: data.start_date,
        end_date: data.end_date,
      };
      if (data.acct_id_filter?.trim()) {
        payload.acct_id_filter = Number(data.acct_id_filter);
      }
      return reportsApi.generate(payload);
    },
    onSuccess: (response) => {
      const result = response.data as ReportGenerateResponse;
      setLastReport(result);
      toast.success(result.message ?? 'Report generated successfully');
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const fc = (key: keyof ReportFormValues) => inputClass(Boolean(errors[key]));

  return (
    <div>
      <PageHeader
        title="Transaction Reports"
        description="Generate transaction reports for a date range"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Reports' },
        ]}
      />

      <div className="max-w-lg space-y-6">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="rounded-lg bg-amber-50 p-2">
              <BarChart3 className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-800">Report Parameters</h3>
              <p className="text-xs text-slate-500">Specify the date range and optional account filter</p>
            </div>
          </div>

          <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-5">
            <FormField label="Start Date" htmlFor="start_date" error={errors.start_date} required>
              <input
                id="start_date"
                type="date"
                {...register('start_date')}
                className={fc('start_date')}
              />
            </FormField>

            <FormField label="End Date" htmlFor="end_date" error={errors.end_date} required>
              <input
                id="end_date"
                type="date"
                {...register('end_date')}
                className={fc('end_date')}
              />
            </FormField>

            <FormField
              label="Account ID Filter"
              htmlFor="acct_id_filter"
              error={errors.acct_id_filter}
              hint="Leave blank to include all accounts"
            >
              <input
                id="acct_id_filter"
                type="text"
                inputMode="numeric"
                placeholder="Optional — filter by account ID"
                {...register('acct_id_filter')}
                className={fc('acct_id_filter')}
              />
            </FormField>

            <button
              type="submit"
              disabled={mutation.isPending}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-60"
            >
              {mutation.isPending && <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />}
              <FileText className="h-4 w-4" />
              Generate Report
            </button>
          </form>
        </div>

        {/* Report result */}
        {lastReport && (
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-5">
            <div className="flex items-center gap-3 mb-3">
              <FileText className="h-5 w-5 text-emerald-600" />
              <p className="text-sm font-semibold text-emerald-800">Report Generated</p>
            </div>
            <div className="space-y-1.5">
              {lastReport.report_id && (
                <div className="flex justify-between text-sm">
                  <span className="text-emerald-700">Report ID</span>
                  <span className="font-mono font-medium text-emerald-900">{lastReport.report_id}</span>
                </div>
              )}
              {lastReport.total_transactions != null && (
                <div className="flex justify-between text-sm">
                  <span className="text-emerald-700">Total Transactions</span>
                  <span className="font-medium text-emerald-900">{lastReport.total_transactions.toLocaleString()}</span>
                </div>
              )}
              <p className="text-sm text-emerald-700 mt-2">{lastReport.message}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
