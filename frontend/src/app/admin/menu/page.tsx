/**
 * Admin Menu Page — placeholder for COADM01 (COADM1A BMS map).
 *
 * Route: /admin/menu
 * COBOL program: COADM01C (Transaction: CA00)
 * BMS mapset: COADM01, map: COADM1A
 *
 * This is a stub page that will be expanded by the Admin module.
 * Access is restricted to user_type='A' (Admin) — enforced by middleware.
 *
 * COADM01C menu options (to be implemented):
 *   1 → COUSR00C → /admin/users (User List)
 *   2 → COUSR01C → /admin/users/add (Add User)
 *   3 → COUSR02C → /admin/users/[id]/edit (Update User)
 *   4 → COUSR03C → /admin/users/[id]/delete (Delete User)
 *   5 → COTRTLIC → /admin/transaction-types (Transaction Type List)
 *   6 → COTRTUPC → /admin/transaction-types/[code] (Transaction Type Edit)
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';
import { AppHeader } from '@/components/layout/AppHeader';

const ADMIN_MENU_OPTIONS = [
  { number: '1', label: 'List/Show Users', route: '/admin/users' },
  { number: '2', label: 'Add User', route: '/admin/users/add' },
  { number: '3', label: 'Update User', route: '/admin/users/edit' },
  { number: '4', label: 'Delete User', route: '/admin/users/delete' },
  { number: '5', label: 'List/Manage Transaction Types', route: '/admin/transaction-types' },
  { number: '6', label: 'Update/Delete Transaction Types', route: '/admin/transaction-types/edit' },
] as const;

export default function AdminMenuPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();

  // Redirect unauthenticated users or non-admins
  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
    } else if (user && user.user_type !== 'A') {
      // Non-admin reached admin menu — redirect to regular menu
      router.replace('/menu');
    }
  }, [isAuthenticated, user, router]);

  const handleLogout = async () => {
    logout();
    if (typeof document !== 'undefined') {
      document.cookie = 'carddemo_auth_token=; path=/; max-age=0';
    }
    router.push('/login');
  };

  if (!user || user.user_type !== 'A') return null;

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <AppHeader programName="COADM01C" transactionId="CA00" />

      <main className="flex-1 px-4 py-8 max-w-2xl mx-auto w-full">
        <div className="bg-gray-900 rounded-lg border border-gray-700 p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-yellow-400 font-bold font-mono text-lg">
              CREDIT CARD DEMO APPLICATION
            </h1>
            <p className="text-yellow-400 font-mono text-sm mt-1">
              ADMINISTRATOR FUNCTIONS
            </p>
            <p className="text-cyan-400 text-sm mt-2">
              Welcome, {user.first_name} {user.last_name} (Admin)
            </p>
          </div>

          {/* Admin badge */}
          <div className="flex justify-center mb-6">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium
                             bg-red-900 text-red-200 border border-red-700">
              Administrator Access
            </span>
          </div>

          {/* Menu options */}
          <div className="space-y-2 mb-8">
            <p className="text-cyan-400 text-sm mb-4">Select an option:</p>
            {ADMIN_MENU_OPTIONS.map((option) => (
              <button
                key={option.number}
                onClick={() => router.push(option.route)}
                className="w-full text-left flex items-center gap-4 px-4 py-2 rounded
                           text-gray-300 hover:bg-gray-800 hover:text-white transition-colors
                           font-mono text-sm"
              >
                <span className="text-blue-400 font-bold w-4">{option.number}</span>
                <span>{option.label}</span>
              </button>
            ))}
          </div>

          {/* PF key bar */}
          <div className="border-t border-gray-700 pt-4">
            <div className="flex gap-4 justify-center">
              <button
                onClick={handleLogout}
                className="btn-secondary text-xs"
              >
                F3=Exit
              </button>
            </div>
            <p className="text-yellow-500 text-xs font-mono text-center mt-2">
              ENTER=Select&nbsp;&nbsp;&nbsp;F3=Exit
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
