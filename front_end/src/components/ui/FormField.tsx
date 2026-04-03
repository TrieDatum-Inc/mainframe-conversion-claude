/**
 * FormField component wrapping a label + input + error.
 *
 * Maps BMS DFHMDF field definitions to accessible form controls.
 * BMS color hints are reflected in label styles.
 */
import { cn } from '@/lib/utils';
import { forwardRef, InputHTMLAttributes } from 'react';

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
  /** readOnly maps to BMS ASKIP attribute (protected field) */
  readOnly?: boolean;
}

const FormField = forwardRef<HTMLInputElement, FormFieldProps>(
  ({ label, error, hint, readOnly, className, id, ...props }, ref) => {
    const fieldId = id || label.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="flex flex-col gap-1">
        <label
          htmlFor={fieldId}
          className={cn(
            'text-sm font-medium',
            readOnly ? 'text-gray-500' : 'text-cyan-700',
          )}
        >
          {label}
          {hint && (
            <span className="ml-2 text-xs font-normal text-blue-600">{hint}</span>
          )}
        </label>
        <input
          ref={ref}
          id={fieldId}
          readOnly={readOnly}
          aria-readonly={readOnly}
          aria-invalid={!!error}
          aria-describedby={error ? `${fieldId}-error` : undefined}
          className={cn(
            'rounded-md border px-3 py-2 text-sm transition-colors',
            'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            readOnly
              ? 'bg-gray-50 border-gray-200 text-gray-700 cursor-default'
              : 'bg-white border-gray-300 text-gray-900 hover:border-gray-400',
            error && 'border-red-500 focus:ring-red-500',
            // Green underline on editable fields (BMS GREEN attribute)
            !readOnly && !error && 'border-b-green-500',
            className,
          )}
          {...props}
        />
        {error && (
          <p id={`${fieldId}-error`} className="text-xs text-red-600" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  },
);
FormField.displayName = 'FormField';

export { FormField };
