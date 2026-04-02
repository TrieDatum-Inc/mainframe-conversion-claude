'use client';

// ============================================================
// Dashboard Page
// Summary view — mirrors the role-based menu system of COMEN01C / COADM01C.
// Provides quick navigation cards and system metrics.
// ============================================================

import Link from 'next/link';
import {
  CreditCard,
  Receipt,
  Users,
  DollarSign,
  Shield,
  Tag,
  BarChart3,
  ArrowRight,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatCard } from '@/components/ui/StatCard';

interface QuickLinkCard {
  href: string;
  title: string;
  description: string;
  icon: React.ElementType;
  iconColor: string;
  adminOnly?: boolean;
}

const QUICK_LINKS: QuickLinkCard[] = [
  {
    href: '/cards',
    title: 'Card Management',
    description: 'View, search, and update credit cards',
    icon: CreditCard,
    iconColor: 'text-blue-600',
  },
  {
    href: '/transactions',
    title: 'Transactions',
    description: 'Browse and add transaction records',
    icon: Receipt,
    iconColor: 'text-violet-600',
  },
  {
    href: '/billing',
    title: 'Bill Payment',
    description: 'Process account bill payments',
    icon: DollarSign,
    iconColor: 'text-emerald-600',
  },
  {
    href: '/reports',
    title: 'Reports',
    description: 'Generate transaction reports by date range',
    icon: BarChart3,
    iconColor: 'text-amber-600',
  },
  {
    href: '/authorizations',
    title: 'Authorizations',
    description: 'View pending authorizations and fraud flags',
    icon: Shield,
    iconColor: 'text-red-600',
  },
  {
    href: '/transaction-types',
    title: 'Transaction Types',
    description: 'View and manage transaction type codes',
    icon: Tag,
    iconColor: 'text-slate-600',
    adminOnly: true,
  },
  {
    href: '/users',
    title: 'User Management',
    description: 'Create and manage system users',
    icon: Users,
    iconColor: 'text-violet-600',
    adminOnly: true,
  },
];

export default function DashboardPage() {
  const { user, isAdmin } = useAuth();

  const visibleLinks = QUICK_LINKS.filter(
    (link) => !link.adminOnly || isAdmin,
  );

  return (
    <div>
      <PageHeader
        title={`Welcome, ${user?.first_name ?? 'User'}`}
        description={`Signed in as ${user?.user_id} · ${isAdmin ? 'Administrator' : 'User'}`}
      />

      {/* Quick access links */}
      <section>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">
          Quick Access
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {visibleLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="group bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md hover:border-blue-200 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`rounded-lg bg-slate-50 p-2 ${link.iconColor}`}>
                  <link.icon className="h-5 w-5" />
                </div>
                <ArrowRight className="h-4 w-4 text-slate-300 group-hover:text-blue-500 group-hover:translate-x-0.5 transition-all" />
              </div>
              <h3 className="text-sm font-semibold text-slate-900">
                {link.title}
              </h3>
              <p className="mt-1 text-xs text-slate-500 leading-relaxed">
                {link.description}
              </p>
            </Link>
          ))}
        </div>
      </section>

      {/* Account lookup shortcut */}
      <section className="mt-8">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">
          Account Lookup
        </h2>
        <AccountLookupCard />
      </section>
    </div>
  );
}

function AccountLookupCard() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm max-w-md">
      <h3 className="text-sm font-semibold text-slate-900 mb-1">
        View Account Details
      </h3>
      <p className="text-xs text-slate-500 mb-4">
        Enter an account ID to view full account and customer information
      </p>
      <form
        action="/accounts"
        method="get"
        onSubmit={(e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const input = form.querySelector('input') as HTMLInputElement;
          if (input.value.trim()) {
            window.location.href = `/accounts/${input.value.trim()}`;
          }
        }}
        className="flex gap-2"
      >
        <input
          type="text"
          name="acctId"
          placeholder="Account ID"
          inputMode="numeric"
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          Go
        </button>
      </form>
    </div>
  );
}
