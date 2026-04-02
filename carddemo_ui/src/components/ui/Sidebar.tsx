'use client';

// ============================================================
// Sidebar Navigation
// Maps COMEN01C (user menu) and COADM01C (admin menu) options
// to grouped nav links. Admin sections hidden for user type 'U'.
// ============================================================

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  CreditCard,
  Receipt,
  Users,
  FileText,
  DollarSign,
  BarChart3,
  Shield,
  LogOut,
  Building2,
  Tag,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  adminOnly?: boolean;
}

interface NavGroup {
  label: string;
  items: NavItem[];
  adminOnly?: boolean;
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Overview',
    items: [
      { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    ],
  },
  {
    label: 'Card Management',
    items: [
      { href: '/cards', label: 'Cards', icon: CreditCard },
      { href: '/transactions', label: 'Transactions', icon: Receipt },
      { href: '/billing', label: 'Bill Payment', icon: DollarSign },
      { href: '/reports', label: 'Reports', icon: BarChart3 },
    ],
  },
  {
    label: 'Authorizations',
    items: [
      { href: '/authorizations', label: 'Authorizations', icon: Shield },
    ],
  },
  {
    label: 'Administration',
    adminOnly: true,
    items: [
      { href: '/users', label: 'Users', icon: Users, adminOnly: true },
      { href: '/transaction-types', label: 'Transaction Types', icon: Tag, adminOnly: true },
    ],
  },
];

function NavGroupSection({
  group,
  isAdmin,
}: {
  group: NavGroup;
  isAdmin: boolean;
}) {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(true);

  if (group.adminOnly && !isAdmin) return null;

  const visibleItems = group.items.filter(
    (item) => !item.adminOnly || isAdmin,
  );

  if (visibleItems.length === 0) return null;

  return (
    <div className="mb-1">
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-3 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider hover:text-slate-600 transition-colors"
      >
        {group.label}
        {isOpen ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
      </button>

      {isOpen && (
        <ul className="mt-1 space-y-0.5">
          {visibleItems.map((item) => {
            const isActive =
              item.href === '/dashboard'
                ? pathname === '/dashboard'
                : pathname.startsWith(item.href);

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <item.icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export function Sidebar() {
  const { user, isAdmin, logout } = useAuth();

  return (
    <aside className="flex h-full w-64 flex-col bg-white border-r border-slate-200">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-200">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 shrink-0">
          <Building2 className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-slate-900">CardDemo</p>
          <p className="text-xs text-slate-400">Credit Card System</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {NAV_GROUPS.map((group) => (
          <NavGroupSection key={group.label} group={group} isAdmin={isAdmin} />
        ))}
      </nav>

      {/* User info + Logout — mirrors COMEN01C option 0 (exit) */}
      <div className="border-t border-slate-200 p-3">
        <div className="flex items-center gap-3 rounded-lg px-2 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 shrink-0">
            <span className="text-xs font-bold text-blue-700">
              {(user?.first_name?.[0] ?? '') + (user?.last_name?.[0] ?? '')}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-700 truncate">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="text-xs text-slate-400 truncate">
              {isAdmin ? 'Administrator' : 'User'} · {user?.user_id}
            </p>
          </div>
        </div>
        <button
          onClick={logout}
          className="mt-1 flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm text-slate-500 hover:bg-red-50 hover:text-red-600 transition-colors"
          aria-label="Sign out (PF3 equivalent)"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
