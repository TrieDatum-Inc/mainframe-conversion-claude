'use client';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
}

const SIZE_CLASSES = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-[3px]',
};

export function LoadingSpinner({ size = 'md', label }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div
        className={`rounded-full border-slate-200 border-t-blue-600 animate-spin ${SIZE_CLASSES[size]}`}
        role="status"
        aria-label={label ?? 'Loading'}
      />
      {label && <p className="text-sm text-slate-500">{label}</p>}
    </div>
  );
}

export function LoadingSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="animate-pulse space-y-3">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 rounded bg-slate-200"
          style={{ width: `${85 - i * 10}%` }}
        />
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="animate-pulse">
      <div className="mb-3 h-10 rounded bg-slate-100" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="mb-2 flex gap-4">
          {Array.from({ length: cols }).map((_, j) => (
            <div key={j} className="h-8 flex-1 rounded bg-slate-100" />
          ))}
        </div>
      ))}
    </div>
  );
}
