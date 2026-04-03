/**
 * StatusMessage component.
 *
 * Maps to the ERRMSG field on all COUSR0x BMS maps:
 *   Row 23, Col 1, Length 78, ASKIP,BRT,FSET
 *   Color: RED for errors, GREEN for success
 *
 * COUSR01C: success message in DFHGREEN, errors in DFHRED (default).
 * COUSR02C: success in DFHGREEN, no-change in DFHRED.
 * COUSR03C: success in DFHGREEN after DELETE, errors in DFHRED.
 */
import { cn } from '@/lib/utils';

interface StatusMessageProps {
  message: string | null;
  type: 'success' | 'error' | 'info';
  className?: string;
}

export function StatusMessage({ message, type, className }: StatusMessageProps) {
  if (!message) return null;

  return (
    <div
      role="alert"
      aria-live="polite"
      className={cn(
        'rounded-md px-4 py-3 text-sm font-medium',
        {
          // DFHGREEN — success messages (user added/updated/deleted)
          'bg-green-50 border border-green-300 text-green-800': type === 'success',
          // DFHRED — error messages (validation, not found, duplicate)
          'bg-red-50 border border-red-300 text-red-800': type === 'error',
          // DFHNEUTR — informational ('Press PF5 key to save...')
          'bg-blue-50 border border-blue-300 text-blue-800': type === 'info',
        },
        className,
      )}
    >
      {message}
    </div>
  );
}
