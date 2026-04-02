'use client';

import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  iconColor?: string;
  trend?: {
    value: string;
    positive: boolean;
  };
}

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-blue-600',
  trend,
}: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-500 truncate">{title}</p>
          <p className="mt-2 text-3xl font-bold text-slate-900 truncate">{value}</p>
          {subtitle && (
            <p className="mt-1 text-xs text-slate-400 truncate">{subtitle}</p>
          )}
          {trend && (
            <p
              className={`mt-2 text-xs font-medium ${
                trend.positive ? 'text-emerald-600' : 'text-red-500'
              }`}
            >
              {trend.positive ? '+' : ''}{trend.value}
            </p>
          )}
        </div>
        <div className={`ml-4 shrink-0 rounded-lg bg-slate-50 p-2.5 ${iconColor}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}
