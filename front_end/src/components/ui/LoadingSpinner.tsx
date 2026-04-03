'use client'

interface LoadingSpinnerProps {
  message?: string
}

export function LoadingSpinner({ message = 'Processing...' }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center py-8 gap-3">
      <div
        className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"
        aria-hidden="true"
      />
      <p className="text-sm text-gray-600">{message}</p>
    </div>
  )
}
