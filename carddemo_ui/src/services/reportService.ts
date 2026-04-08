/**
 * Report service — wraps /api/v1/reports/* endpoints.
 * Derived from CORPT00C (CICS transaction CR00).
 */
import client from './apiClient';
import type { ReportJob, ReportSubmitRequest } from '@/lib/types/api';

export const reportService = {
  /**
   * POST /api/v1/reports/transactions
   * Derived from CORPT00C PROCESS-ENTER-KEY → SUBMIT-JOB-TO-INTRDR.
   * Returns HTTP 202 (async) — equivalent to JCL submission via TDQ.
   */
  async submitReport(request: ReportSubmitRequest): Promise<ReportJob> {
    const { data } = await client.post<ReportJob>('/reports/transactions', request);
    return data;
  },

  /**
   * GET /api/v1/reports/transactions/{job_id}
   * No COBOL equivalent — added for REST observability.
   */
  async getReportJob(jobId: string): Promise<ReportJob> {
    const { data } = await client.get<ReportJob>(`/reports/transactions/${jobId}`);
    return data;
  },
};
