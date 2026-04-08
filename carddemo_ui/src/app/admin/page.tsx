/**
 * Admin menu page — derived from COADM01C (CICS transaction CA00).
 * BMS map: COADM01 (COADM1A)
 *
 * Shows admin navigation menu (8 options from CDEMO-ADMIN-OPT-* arrays).
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { Alert } from '@/components/ui/Alert';
import { authService } from '@/services/authService';
import { adminService } from '@/services/adminService';
import { ROUTES } from '@/lib/constants/routes';
import type { AdminMenuResponse } from '@/lib/types/api';

export default function AdminPage() {
  const router = useRouter();
  const [menu, setMenu] = useState<AdminMenuResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authService.isAdmin()) {
      router.replace(ROUTES.DASHBOARD);
      return;
    }
    adminService
      .getAdminMenu()
      .then(setMenu)
      .catch(() => setError('Failed to load admin menu'))
      .finally(() => setIsLoading(false));
  }, [router]);

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Admin Menu</h1>
            <p className="page-subtitle">COADM01C — CA00</p>
          </div>
        </div>

        {error && <Alert variant="error" className="mb-4">{error}</Alert>}

        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin h-6 w-6 rounded-full border-4 border-blue-600 border-t-transparent" />
          </div>
        ) : menu ? (
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">{menu.menu_title}</h2>
            <div className="divide-y divide-gray-100">
              {menu.menu_items.map((item) => (
                <div
                  key={item.option_number}
                  className="flex items-center justify-between py-3"
                >
                  <div className="flex items-center gap-3">
                    <span className="h-7 w-7 flex items-center justify-center rounded-full bg-blue-100 text-blue-700 text-sm font-semibold">
                      {item.option_number}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{item.name}</p>
                      {!item.is_installed && (
                        <p className="text-xs text-gray-400">This option is not installed</p>
                      )}
                    </div>
                  </div>
                  {item.is_installed && (
                    <Link
                      href={getAdminRoute(item.rest_endpoint)}
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Open &rarr;
                    </Link>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}

function getAdminRoute(restEndpoint: string): string {
  // Map API endpoint paths to UI routes
  if (restEndpoint.includes('/admin/users')) return ROUTES.ADMIN_USERS;
  if (restEndpoint.includes('/reports')) return ROUTES.ADMIN_REPORTS;
  if (restEndpoint.includes('/transaction-types')) return ROUTES.ADMIN_TRANSACTION_TYPES;
  if (restEndpoint.includes('/accounts')) return ROUTES.ACCOUNTS;
  if (restEndpoint.includes('/cards')) return ROUTES.CARDS;
  if (restEndpoint.includes('/transactions')) return ROUTES.TRANSACTIONS;
  if (restEndpoint.includes('/authorizations')) return ROUTES.AUTHORIZATIONS;
  return ROUTES.DASHBOARD;
}
