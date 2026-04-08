/**
 * Reports page — derived from CORPT00C (CICS transaction CR00).
 * BMS map: CORPT00 (CORPT0A)
 *
 * COBOL rules preserved:
 *   - report_type: monthly / yearly / custom
 *   - custom: start_date + end_date required
 *   - start_date <= end_date
 *   - Returns job_id immediately (async, like JCL TDQ submission)
 */
'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { FormField, Input, Select } from '@/components/ui/FormField';
import { Alert } from '@/components/ui/Alert';
import { reportService } from '@/services/reportService';
import { reportSubmitSchema, type ReportFormValues } from '@/lib/validators/report';
import { extractErrorMessage } from '@/services/apiClient';
import type { ReportJob } from '@/lib/types/api';

export default function ReportsPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [job, setJob] = useState<ReportJob | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ReportFormValues>({
    resolver: zodResolver(reportSubmitSchema),
    defaultValues: { report_type: 'monthly' },
  });

  const reportType = watch('report_type');

  const onSubmit = async (values: ReportFormValues) => {
    setIsSubmitting(true);
    setSubmitError(null);
    setJob(null);
    try {
      const result = await reportService.submitReport({
        report_type: values.report_type,
        start_date: values.start_date || undefined,
        end_date: values.end_date || undefined,
      });
      setJob(result);
    } catch (err) {
      setSubmitError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Transaction Reports</h1>
            <p className="page-subtitle">CORPT00C — CR00</p>
          </div>
        </div>

        {submitError && <Alert variant="error" className="mb-4">{submitError}</Alert>}

        {job && (
          <Alert variant="success" className="mb-4">
            <p className="font-semibold">Report job submitted successfully</p>
            <p className="text-sm mt-1">
              Job ID: <span className="font-mono">{job.job_id}</span>
            </p>
            <p className="text-sm">
              Period: {job.start_date} to {job.end_date}
            </p>
            <p className="text-sm">Status: {job.status}</p>
            {job.message && <p className="text-sm mt-1">{job.message}</p>}
          </Alert>
        )}

        <div className="card">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <FormField
              label="Report Type"
              htmlFor="report_type"
              error={errors.report_type?.message}
              required
            >
              <Select id="report_type" {...register('report_type')}>
                <option value="monthly">Monthly — current month</option>
                <option value="yearly">Yearly — current year</option>
                <option value="custom">Custom — specify date range</option>
              </Select>
            </FormField>

            {reportType === 'custom' && (
              <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                <FormField
                  label="Start Date"
                  htmlFor="start_date"
                  error={errors.start_date?.message}
                  hint="YYYY-MM-DD (SDTYYYYI/SDTMMI/SDTDDI)"
                  required
                >
                  <Input
                    id="start_date"
                    type="date"
                    hasError={!!errors.start_date}
                    {...register('start_date')}
                  />
                </FormField>

                <FormField
                  label="End Date"
                  htmlFor="end_date"
                  error={errors.end_date?.message}
                  hint="YYYY-MM-DD (EDTYYYYI/EDTMMI/EDTDDI)"
                  required
                >
                  <Input
                    id="end_date"
                    type="date"
                    hasError={!!errors.end_date}
                    {...register('end_date')}
                  />
                </FormField>
              </div>
            )}

            {/* CORPT00C: must confirm before submission */}
            <p className="text-sm text-gray-600 bg-blue-50 border border-blue-200 rounded-lg p-3">
              Click &quot;Submit Report&quot; to queue the report job. The report will be generated asynchronously
              (equivalent to CORPT00C EXEC CICS WRITEQ TD QUEUE(&apos;JOBS&apos;)).
            </p>

            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
              className="w-full"
            >
              Submit Report
            </Button>
          </form>
        </div>
      </div>
    </AppShell>
  );
}
