/**
 * API service layer for CardDemo Batch Processing Module.
 * Centralizes all API calls to the FastAPI backend.
 */

import axios, { AxiosError } from 'axios'
import type {
  BatchJobResponse,
  ExportResponse,
  ImportRequest,
  ImportResponse,
  InterestCalculationRequest,
  InterestCalculationResponse,
  TransactionPostingRequest,
  TransactionPostingResponse,
  TransactionReportRequest,
  TransactionReportResponse,
} from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/batch`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // Batch jobs can take time
})

// ============================================================
// Error handling
// ============================================================

function extractErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    return error.response?.data?.detail || error.message || 'An unexpected error occurred'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unexpected error occurred'
}

// ============================================================
// CBTRN02C — Transaction Posting
// ============================================================

export async function postTransactions(
  request: TransactionPostingRequest
): Promise<TransactionPostingResponse> {
  try {
    const response = await apiClient.post<TransactionPostingResponse>(
      '/transaction-posting',
      request
    )
    return response.data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}

// ============================================================
// CBTRN03C — Transaction Report
// ============================================================

export async function generateTransactionReport(
  request: TransactionReportRequest
): Promise<TransactionReportResponse> {
  try {
    const response = await apiClient.post<TransactionReportResponse>(
      '/transaction-report',
      request
    )
    return response.data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}

// ============================================================
// CBACT04C — Interest Calculation
// ============================================================

export async function calculateInterest(
  request: InterestCalculationRequest
): Promise<InterestCalculationResponse> {
  try {
    const response = await apiClient.post<InterestCalculationResponse>(
      '/interest-calculation',
      request
    )
    return response.data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}

// ============================================================
// CBEXPORT — Data Export
// ============================================================

export async function exportData(): Promise<ExportResponse> {
  try {
    const response = await apiClient.get<ExportResponse>('/export')
    return response.data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}

// ============================================================
// CBIMPORT — Data Import
// ============================================================

export async function importData(request: ImportRequest): Promise<ImportResponse> {
  try {
    const response = await apiClient.post<ImportResponse>('/import', request)
    return response.data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}

// ============================================================
// Job Status
// ============================================================

export async function getJobStatus(jobId: number): Promise<BatchJobResponse> {
  try {
    const response = await apiClient.get<BatchJobResponse>(`/jobs/${jobId}`)
    return response.data
  } catch (error) {
    throw new Error(extractErrorMessage(error))
  }
}
