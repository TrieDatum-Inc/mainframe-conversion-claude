'use client';

// ============================================================
// Badge — Status indicators
// Used for active/inactive, admin/user, approved/declined
// ============================================================

type BadgeVariant =
  | 'active'
  | 'inactive'
  | 'admin'
  | 'user'
  | 'approved'
  | 'declined'
  | 'pending'
  | 'success'
  | 'warning'
  | 'error'
  | 'neutral';

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  active:   'bg-emerald-100 text-emerald-800 ring-emerald-200',
  inactive: 'bg-slate-100 text-slate-600 ring-slate-200',
  admin:    'bg-violet-100 text-violet-800 ring-violet-200',
  user:     'bg-blue-100 text-blue-800 ring-blue-200',
  approved: 'bg-emerald-100 text-emerald-800 ring-emerald-200',
  declined: 'bg-red-100 text-red-800 ring-red-200',
  pending:  'bg-amber-100 text-amber-800 ring-amber-200',
  success:  'bg-emerald-100 text-emerald-800 ring-emerald-200',
  warning:  'bg-amber-100 text-amber-800 ring-amber-200',
  error:    'bg-red-100 text-red-800 ring-red-200',
  neutral:  'bg-slate-100 text-slate-700 ring-slate-200',
};

interface BadgeProps {
  variant: BadgeVariant;
  label: string;
  className?: string;
}

export function Badge({ variant, label, className = '' }: BadgeProps) {
  const variantClass = VARIANT_CLASSES[variant] ?? VARIANT_CLASSES.neutral;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${variantClass} ${className}`}
    >
      {label}
    </span>
  );
}

/** Derive badge variant from a generic status string */
export function statusBadge(status: string | undefined | null): BadgeVariant {
  const s = (status ?? '').toUpperCase();
  if (s === 'Y' || s === 'ACTIVE' || s === 'A') return 'active';
  if (s === 'N' || s === 'INACTIVE' || s === 'I') return 'inactive';
  return 'neutral';
}

/** Derive badge variant for user type */
export function userTypeBadge(type: string | undefined | null): BadgeVariant {
  return (type ?? '').toUpperCase() === 'A' ? 'admin' : 'user';
}
