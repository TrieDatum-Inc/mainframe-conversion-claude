/**
 * Main Menu Page — placeholder for COMEN01 (COMEN1A BMS map).
 *
 * Route: /menu
 * COBOL program: COMEN01C (Transaction: CM00)
 * BMS mapset: COMEN01, map: COMEN1A
 *
 * This is a stub page that will be expanded by the Menu module.
 * Currently shows the authenticated user's info and navigation links
 * to demonstrate the auth flow is working end-to-end.
 *
 * COMEN01C menu options (to be implemented):
 *   1 → COBIL00C  → /billing/payment
 *   2 → COACTVWC  → /accounts/view
 *   3 → COTRN01C  → /transactions/[id]
 *   4 → COTRN00C  → /transactions
 *   5 → COCRDSLC  → /cards/view
 *   6 → COCRDLIC  → /cards
 *   7 → CORPT00C  → /reports/request
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';
import { AppHeader } from '@/components/layout/AppHeader';

const MENU_OPTIONS = [
  { number: '1', label: 'View/Add/Update Account Information', route: '/accounts/view' },
  { number: '2', label: 'Account Inquiry (View Only)', route: '/accounts/view' },
  { number: '3', label: 'View/Add/Update Transaction Information', route: '/transactions' },
  { number: '4', label: 'View Transactions by Account/Card', route: '/transactions' },
  { number: '5', label: 'View/Update Credit Card Information', route: '/cards/view' },
  { number: '6', label: 'List Credit Cards', route: '/cards' },
  { number: '7', label: 'Generate Transaction Report', route: '/reports/request' },
] as const;

export default function MenuPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();

  // Redirect unauthenticated users to login
  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, router]);

  const handleLogout = async () => {
    logout();
    if (typeof document !== 'undefined') {
      document.cookie = 'carddemo_auth_token=; path=/; max-age=0';
    }
    router.push('/login');
  };

  if (!user) return null;

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <AppHeader programName="COMEN01C" transactionId="CM00" />

      <main className="flex-1 px-4 py-8 max-w-2xl mx-auto w-full">
        <div className="bg-gray-900 rounded-lg border border-gray-700 p-8">
          {/* Welcome header */}
          <div className="text-center mb-8">
            <h1 className="text-yellow-400 font-bold font-mono text-lg">
              CREDIT CARD DEMO APPLICATION
            </h1>
            <p className="text-cyan-400 text-sm mt-2">
              Welcome, {user.first_name} {user.last_name}
            </p>
          </div>

          {/* Menu options */}
          <div className="space-y-2 mb-8">
            <p className="text-cyan-400 text-sm mb-4">Select an option:</p>
            {MENU_OPTIONS.map((option) => (
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
