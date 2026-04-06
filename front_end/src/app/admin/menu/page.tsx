'use client';

/**
 * Admin Menu page — /admin/menu
 *
 * COBOL origin: COADM01C (Transaction OADM), BMS map COADM1A
 *
 * Menu options and routes:
 *   1 - List/Add Users     → /admin/users     (COUSR00C)
 *   2 - Add User           → /admin/users/add  (COUSR01C)
 *   3 - Update User        → /admin/users      (select U from list → COUSR02C)
 *   4 - Delete User        → /admin/users      (select D from list → COUSR03C)
 *   5 - Transaction Types  → /admin/transaction-types (COTRTLIC)
 *   0 - Exit               → /login (logout)
 *
 * Admin only: only user_type='A' should reach this page.
 */

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';

const ADMIN_MENU_OPTIONS = [
  { option: '1', label: 'List/Add Users', route: '/admin/users' },
  { option: '2', label: 'Add User', route: '/admin/users/add' },
  { option: '3', label: 'Update User (select from list)', route: '/admin/users' },
  { option: '4', label: 'Delete User (select from list)', route: '/admin/users' },
  { option: '5', label: 'Manage Transaction Types', route: '/admin/transaction-types' },
  { option: '0', label: 'Exit / Logout', route: '/login' },
] as const;

export default function AdminMenuPage() {
  const router = useRouter();
  const { user, clearAuth } = useAuthStore();
  const [selected, setSelected] = React.useState('');
  const [error, setError] = React.useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const option = ADMIN_MENU_OPTIONS.find((o) => o.option === selected);
    if (!option) {
      setError('Invalid option selected. Please enter a valid number.');
      return;
    }
    if (option.option === '0') {
      clearAuth();
      router.push('/login');
      return;
    }
    router.push(option.route);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-900 text-white py-3 px-6">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-xs text-blue-300">COADM01C | OADM</p>
            <h1 className="text-lg font-bold">CardDemo — Admin Menu</h1>
          </div>
          <div className="text-xs text-blue-300 text-right">
            <p>Logged in as: {user?.user_id ?? '—'}</p>
            <p>Administrator</p>
          </div>
        </div>
      </header>

      <main className="max-w-xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-800 mb-4">
            Select an option:
          </h2>

          <ul className="space-y-2 mb-6">
            {ADMIN_MENU_OPTIONS.map((opt) => (
              <li key={opt.option} className="flex items-center gap-3">
                <span className="w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-700 text-xs font-bold rounded">
                  {opt.option}
                </span>
                <Link
                  href={opt.option === '0' ? '#' : opt.route}
                  onClick={
                    opt.option === '0'
                      ? (e) => { e.preventDefault(); clearAuth(); router.push('/login'); }
                      : undefined
                  }
                  className="text-sm text-blue-700 hover:text-blue-900 hover:underline"
                >
                  {opt.label}
                </Link>
              </li>
            ))}
          </ul>

          {error && (
            <p className="text-red-600 text-xs mb-3">{error}</p>
          )}

          <form onSubmit={handleSubmit} className="flex gap-3 items-end">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Enter option number:
              </label>
              <input
                type="number"
                min={0}
                max={5}
                value={selected}
                onChange={(e) => { setSelected(e.target.value); setError(''); }}
                autoFocus
                className="w-20 border border-gray-300 rounded px-2 py-1.5 text-sm text-right focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors"
            >
              Continue
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
