/**
 * Utility functions for CardDemo batch processing frontend.
 */

import { clsx, type ClassValue } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatCurrency(amount: string | number | null | undefined): string {
  if (amount === null || amount === undefined) return '$0.00'
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (isNaN(num)) return '$0.00'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(num)
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return dateStr
  }
}

export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return dateStr
  }
}

export function getReasonCodeLabel(code: string): string {
  const labels: Record<string, string> = {
    '100': 'Invalid Card Number',
    '101': 'Account Not Found',
    '102': 'Over Credit Limit',
    '103': 'Account Expired',
    '109': 'Account Update Failed',
  }
  return labels[code] || `Unknown (${code})`
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    completed: 'text-green-700 bg-green-50 border-green-200',
    running: 'text-blue-700 bg-blue-50 border-blue-200',
    pending: 'text-yellow-700 bg-yellow-50 border-yellow-200',
    failed: 'text-red-700 bg-red-50 border-red-200',
  }
  return colors[status] || 'text-gray-700 bg-gray-50 border-gray-200'
}

export function todayISOString(): string {
  return new Date().toISOString().split('T')[0]
}
