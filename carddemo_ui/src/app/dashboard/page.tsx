/**
 * Dashboard — derived from COMEN01 (main menu) and COADM01 (admin menu).
 *
 * BMS maps: COMEN1A (user menu), COADM1A (admin menu)
 *
 * COMEN01 options (user):
 *   1. View/Update Account   -> /accounts
 *   2. View/Update Credit Cards -> /cards
 *   3. View/Add Transactions -> /transactions
 *   4. Bill Payments         -> /accounts (payment flow)
 *
 * COADM01 options (admin):
 *   1. View/Update Account
 *   2. View/Update Credit Cards
 *   3. View/Update Transaction Types
 *   4. View/Add Transactions
 *   5. Bill Payments
 *   6. View Authorization History
 *   7. User Management
 *   8. Transaction Reports
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { authService } from '@/services/authService';
import { ROUTES } from '@/lib/constants/routes';
import type { AuthUser } from '@/lib/types/api';

interface MenuItem {
  title: string;
  description: string;
  href: string;
  icon: React.ReactNode;
  adminOnly?: boolean;
  color: string;
}

const menuItems: MenuItem[] = [
  {
    title: 'Accounts',
    description: 'View and update customer account details, balances, and limits',
    href: ROUTES.ACCOUNTS,
    color: 'bg-blue-50 hover:bg-blue-100 border-blue-200 text-blue-700',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-8 w-8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
      </svg>
    ),
  },
  {
    title: 'Credit Cards',
    description: 'Browse and manage credit cards, activation status, and embossed names',
    href: ROUTES.CARDS,
    color: 'bg-purple-50 hover:bg-purple-100 border-purple-200 text-purple-700',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-8 w-8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
      </svg>
    ),
  },
  {
    title: 'Transactions',
    description: 'Browse transaction history, view details, and create new transactions',
    href: ROUTES.TRANSACTIONS,
    color: 'bg-green-50 hover:bg-green-100 border-green-200 text-green-700',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-8 w-8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
      </svg>
    ),
  },
  {
    title: 'Authorizations',
    description: 'Process and review card authorization history, fraud marking',
    href: ROUTES.AUTHORIZATIONS,
    color: 'bg-orange-50 hover:bg-orange-100 border-orange-200 text-orange-700',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-8 w-8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
  },
  {
    title: 'User Management',
    description: 'Add, update, and delete system users (admin only)',
    href: ROUTES.ADMIN_USERS,
    adminOnly: true,
    color: 'bg-indigo-50 hover:bg-indigo-100 border-indigo-200 text-indigo-700',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-8 w-8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
      </svg>
    ),
  },
  {
    title: 'Transaction Types',
    description: 'Browse and manage transaction type codes and descriptions',
    href: ROUTES.ADMIN_TRANSACTION_TYPES,
    adminOnly: true,
    color: 'bg-teal-50 hover:bg-teal-100 border-teal-200 text-teal-700',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-8 w-8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6z" />
      </svg>
    ),
  },
  {
    title: 'Reports',
    description: 'Generate monthly, yearly, or custom transaction reports',
    href: ROUTES.ADMIN_REPORTS,
    color: 'bg-rose-50 hover:bg-rose-100 border-rose-200 text-rose-700',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-8 w-8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
  },
];

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    if (!currentUser) {
      router.replace(ROUTES.LOGIN);
      return;
    }
    setUser(currentUser);
  }, [router]);

  if (!user) return null;

  const isAdmin = user.user_type === 'A';
  const visibleItems = menuItems.filter((item) => !item.adminOnly || isAdmin);
  const displayName = user.first_name
    ? `${user.first_name} ${user.last_name ?? ''}`.trim()
    : user.user_id;

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        {/* Welcome header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {displayName}
          </h1>
          <p className="text-gray-500 mt-1">
            {isAdmin ? 'Administrator Dashboard' : 'Main Menu'} — CardDemo Credit Card Management
          </p>
        </div>

        {/* Menu grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {visibleItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex flex-col gap-4 rounded-xl border-2 p-6 transition-all duration-150
                hover:shadow-md hover:-translate-y-0.5
                ${item.color}
              `}
            >
              <div className="opacity-80">{item.icon}</div>
              <div>
                <h3 className="font-semibold text-base mb-1">{item.title}</h3>
                <p className="text-sm opacity-70 leading-relaxed">{item.description}</p>
              </div>
            </Link>
          ))}
        </div>

        {/* Quick stats strip */}
        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Browse Accounts', href: ROUTES.ACCOUNTS, shortcut: 'Ctrl+A' },
            { label: 'View Cards', href: ROUTES.CARDS, shortcut: 'Ctrl+C' },
            { label: 'Transactions', href: ROUTES.TRANSACTIONS, shortcut: 'Ctrl+T' },
            ...(isAdmin ? [{ label: 'Manage Users', href: ROUTES.ADMIN_USERS, shortcut: 'Ctrl+U' }] : []),
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center justify-between rounded-lg bg-white border border-gray-200 px-4 py-3 text-sm hover:bg-gray-50 transition-colors"
            >
              <span className="font-medium text-gray-700">{item.label}</span>
              <span className="text-xs text-gray-400 font-mono">{item.shortcut}</span>
            </Link>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
