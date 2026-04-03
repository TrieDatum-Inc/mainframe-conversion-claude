'use client'

import { cn } from '@/lib/utils'

interface AlertBannerProps {
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  className?: string
}

const styles = {
  success: 'bg-green-50 border-green-200 text-green-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
}

const icons = {
  success: '✓',
  error: '✗',
  warning: '⚠',
  info: 'ℹ',
}

export function AlertBanner({ type, title, message, className }: AlertBannerProps) {
  return (
    <div className={cn('border rounded-md p-4', styles[type], className)} role="alert">
      <div className="flex items-start gap-2">
        <span className="font-bold text-lg leading-none">{icons[type]}</span>
        <div>
          <p className="font-medium">{title}</p>
          {message && <p className="text-sm mt-1 opacity-90">{message}</p>}
        </div>
      </div>
    </div>
  )
}
