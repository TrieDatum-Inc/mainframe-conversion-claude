/**
 * FormField component — wraps an input with a label and error message.
 * Used across all screen form conversions.
 */
import React from 'react';
import { cn } from '@/lib/utils/cn';

interface FormFieldProps {
  label: string;
  htmlFor: string;
  error?: string;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
  className?: string;
}

export function FormField({
  label,
  htmlFor,
  error,
  hint,
  required,
  children,
  className,
}: FormFieldProps) {
  return (
    <div className={cn('flex flex-col gap-1', className)}>
      <label htmlFor={htmlFor} className="field-label">
        {label}
        {required && <span className="ml-1 text-red-500" aria-hidden="true">*</span>}
      </label>
      {children}
      {hint && !error && (
        <p className="text-xs text-gray-500">{hint}</p>
      )}
      {error && (
        <p className="text-xs text-red-600" role="alert" aria-live="polite">
          {error}
        </p>
      )}
    </div>
  );
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ hasError, className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        hasError ? 'field-input-error' : 'field-input',
        className
      )}
      {...props}
    />
  )
);
Input.displayName = 'Input';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  hasError?: boolean;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ hasError, className, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        'block w-full rounded-md border px-3 py-2 text-sm',
        'focus:outline-none focus:ring-1',
        hasError
          ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
          : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
        'disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500',
        className
      )}
      {...props}
    />
  )
);
Select.displayName = 'Select';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  hasError?: boolean;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ hasError, className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        'block w-full rounded-md border px-3 py-2 text-sm',
        'focus:outline-none focus:ring-1',
        hasError
          ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
          : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
        'disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500',
        'resize-none',
        className
      )}
      {...props}
    />
  )
);
Textarea.displayName = 'Textarea';
