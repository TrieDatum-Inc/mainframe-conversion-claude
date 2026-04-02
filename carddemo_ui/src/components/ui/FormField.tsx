'use client';

// ============================================================
// FormField — Wrapper providing label + error display
// Used across all form pages. Aligns to BMS field definitions
// where each BMS field has a corresponding label field.
// ============================================================

import type { FieldError } from 'react-hook-form';

interface FormFieldProps {
  label: string;
  htmlFor?: string;
  error?: FieldError | { message?: string };
  required?: boolean;
  hint?: string;
  children: React.ReactNode;
  className?: string;
}

export function FormField({
  label,
  htmlFor,
  error,
  required,
  hint,
  children,
  className = '',
}: FormFieldProps) {
  const hasError = Boolean(error?.message);

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <label
        htmlFor={htmlFor}
        className="text-sm font-medium text-slate-700"
      >
        {label}
        {required && <span className="ml-0.5 text-red-500">*</span>}
      </label>
      {children}
      {hint && !hasError && (
        <p className="text-xs text-slate-400">{hint}</p>
      )}
      {hasError && (
        <p className="text-xs text-red-600" role="alert">
          {error!.message}
        </p>
      )}
    </div>
  );
}

/** Base input class — apply to all text inputs */
export const INPUT_BASE =
  'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-slate-50 disabled:text-slate-500 transition-colors';

/** Input class with error state */
export function inputClass(hasError: boolean): string {
  return hasError
    ? `${INPUT_BASE} border-red-400 focus:ring-red-500`
    : INPUT_BASE;
}
