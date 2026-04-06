"use client";

/**
 * Sidebar navigation component.
 *
 * Modernizes COMEN01C / COADM01C menu navigation.
 * Instead of a numbered list (option 01-11), we render a sidebar nav.
 *
 * The menu items below map 1-to-1 with the COMEN02Y and COADM02Y arrays.
 * Admin-only items (USRTYPE='A') are hidden for regular users, matching
 * the access control logic in COMEN01C where admin-only options show
 * "No access" error.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  adminOnly: boolean;
}

// Maps to COMEN02Y array (regular user menu options 01-11)
const USER_NAV_ITEMS: NavItem[] = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: <HomeIcon />,
    adminOnly: false,
  },
  {
    href: "/accounts/view",
    label: "Account View",
    icon: <AccountIcon />,
    adminOnly: false,
  },
  {
    href: "/accounts/update",
    label: "Account Update",
    icon: <EditIcon />,
    adminOnly: false,
  },
  {
    href: "/cards",
    label: "Credit Cards",
    icon: <CardIcon />,
    adminOnly: false,
  },
  {
    href: "/transactions",
    label: "Transactions",
    icon: <TransactionIcon />,
    adminOnly: false,
  },
  {
    href: "/reports",
    label: "Reports",
    icon: <ReportIcon />,
    adminOnly: false,
  },
  {
    href: "/bill-payment",
    label: "Bill Payment",
    icon: <BillIcon />,
    adminOnly: false,
  },
  {
    href: "/authorizations",
    label: "Authorizations",
    icon: <AuthIcon />,
    adminOnly: false,
  },
];

// Maps to COADM02Y array (admin menu options 01-06)
const ADMIN_NAV_ITEMS: NavItem[] = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: <HomeIcon />,
    adminOnly: false,
  },
  {
    href: "/admin/users",
    label: "User Management",
    icon: <UsersIcon />,
    adminOnly: true,
  },
  {
    href: "/admin/transaction-types",
    label: "Transaction Types",
    icon: <TransactionIcon />,
    adminOnly: true,
  },
];

export function Sidebar() {
  const { isAdmin } = useAuth();
  const pathname = usePathname();

  const navItems = isAdmin ? ADMIN_NAV_ITEMS : USER_NAV_ITEMS;

  return (
    <aside className="w-56 min-h-screen bg-slate-900 text-slate-300 flex flex-col py-4 px-2 shrink-0">
      <nav aria-label="Main navigation">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive
                      ? "bg-blue-600 text-white font-medium"
                      : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                  }`}
                  aria-current={isActive ? "page" : undefined}
                >
                  <span className="w-4 h-4 shrink-0" aria-hidden="true">
                    {item.icon}
                  </span>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer — transaction ID info (replaces BMS TRNNAME display) */}
      <div className="mt-auto px-3 pt-4 border-t border-slate-700">
        <p className="text-xs text-slate-500">
          {isAdmin ? "Admin Console (CA00)" : "User Portal (CM00)"}
        </p>
        <p className="text-xs text-slate-600 mt-0.5">CardDemo v1.0</p>
      </div>
    </aside>
  );
}

// Icon components (inline SVG to avoid extra dependencies)
function HomeIcon() {
  return (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    </svg>
  );
}

function AccountIcon() {
  return (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  );
}

function EditIcon() {
  return (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  );
}

function CardIcon() {
  return (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
    </svg>
  );
}

function TransactionIcon() {
  return (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    </svg>
  );
}

function ReportIcon() {
  return (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );
}

function BillIcon() {
  return (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  );
}

function AuthIcon() {
  return (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  );
}

function UsersIcon() {
  return (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  );
}
