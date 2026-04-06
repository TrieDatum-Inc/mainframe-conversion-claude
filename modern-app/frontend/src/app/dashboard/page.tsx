"use client";

/**
 * Dashboard page — /dashboard
 *
 * Modern web equivalent of COMEN01C (regular user) and COADM01C (admin).
 *
 * COBOL → Web mapping:
 *   COMEN02Y option array (11 items) → UserDashboard card grid
 *   COADM02Y option array (6 items)  → AdminDashboard card grid
 *   CDEMO-USER-TYPE = 'U'            → UserDashboard rendered
 *   CDEMO-USER-TYPE = 'A'            → AdminDashboard rendered
 *
 * Access control:
 *   COBOL: "No access" error for admin-only options selected by regular users
 *   Web:   Admin cards are never shown to regular users (hidden at render time)
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Header } from "@/components/Layout/Header";
import { Sidebar } from "@/components/Layout/Sidebar";

interface DashboardCard {
  id: string;
  title: string;
  description: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
}

// Maps to COMEN02Y options 01-11 (regular user menu)
const USER_CARDS: DashboardCard[] = [
  {
    id: "account-view",
    title: "Account View",
    description: "View your account details, balance, and credit information",
    href: "/accounts/view",
    icon: <UserCircleIcon />,
    badge: "01",
  },
  {
    id: "account-update",
    title: "Account Update",
    description: "Update your account profile and preferences",
    href: "/accounts/update",
    icon: <PencilIcon />,
    badge: "02",
  },
  {
    id: "credit-card-list",
    title: "Credit Card List",
    description: "View and manage all your credit cards",
    href: "/cards",
    icon: <CardIcon />,
    badge: "03",
  },
  {
    id: "transactions",
    title: "Transaction List",
    description: "Browse your transaction history and search by date",
    href: "/transactions",
    icon: <ListIcon />,
    badge: "06",
  },
  {
    id: "transaction-add",
    title: "Add Transaction",
    description: "Record a new credit card transaction",
    href: "/transactions/add",
    icon: <PlusCircleIcon />,
    badge: "08",
  },
  {
    id: "reports",
    title: "Transaction Reports",
    description: "Generate reports on spending and transactions",
    href: "/reports",
    icon: <ChartIcon />,
    badge: "09",
  },
  {
    id: "bill-payment",
    title: "Bill Payment",
    description: "Pay your credit card bill and manage payments",
    href: "/bill-payment",
    icon: <BankIcon />,
    badge: "10",
  },
  {
    id: "authorizations",
    title: "Pending Authorizations",
    description: "View and act on pending card authorization requests",
    href: "/authorizations",
    icon: <ShieldIcon />,
    badge: "11",
  },
];

// Maps to COADM02Y options 01-06 (admin menu)
const ADMIN_CARDS: DashboardCard[] = [
  {
    id: "user-list",
    title: "User Management",
    description: "View, add, update, and delete CardDemo user accounts",
    href: "/admin/users",
    icon: <UsersIcon />,
    badge: "01-04",
  },
  {
    id: "transaction-types",
    title: "Transaction Types",
    description: "Maintain transaction type reference data (DB2)",
    href: "/admin/transaction-types",
    icon: <TagIcon />,
    badge: "05-06",
  },
];

export default function DashboardPage() {
  const { user, isAuthenticated, isLoading, isAdmin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  const cards = isAdmin ? ADMIN_CARDS : USER_CARDS;
  const menuLabel = isAdmin ? "Admin Console" : "Main Menu";

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 overflow-auto">
          {/* Page heading */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">
              Welcome back, {user?.first_name || user?.user_id}
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              {isAdmin
                ? "Administrator Dashboard — manage users and transaction types"
                : "Your credit card management portal — select a module to get started"}
            </p>
          </div>

          {/* User type badge */}
          <div className="mb-5">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                isAdmin
                  ? "bg-purple-100 text-purple-700"
                  : "bg-blue-100 text-blue-700"
              }`}
            >
              {isAdmin ? "Administrator (A)" : "Regular User (U)"}
              <span className="text-gray-400">|</span>
              {menuLabel}
            </span>
          </div>

          {/* Dashboard cards — replace numbered BMS menu options */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {cards.map((card) => (
              <a
                key={card.id}
                href={card.href}
                className="card group hover:shadow-md hover:border-blue-200 transition-all cursor-pointer block"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center shrink-0 group-hover:bg-blue-100 transition-colors">
                    <span className="w-5 h-5 text-blue-600">{card.icon}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h2 className="text-sm font-semibold text-gray-900 truncate">{card.title}</h2>
                      {card.badge && (
                        <span className="text-xs text-gray-400 shrink-0">#{card.badge}</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{card.description}</p>
                  </div>
                </div>
              </a>
            ))}
          </div>

          {/* System info footer (replaces BMS TRNNAME/PGMNAME/APPLID fields) */}
          <div className="mt-8 p-4 bg-white rounded-lg border border-gray-200 text-xs text-gray-400">
            <div className="flex flex-wrap gap-4">
              <span>
                <strong className="text-gray-500">Program:</strong>{" "}
                {isAdmin ? "COADM01C (CA00)" : "COMEN01C (CM00)"}
              </span>
              <span>
                <strong className="text-gray-500">User ID:</strong> {user?.user_id}
              </span>
              <span>
                <strong className="text-gray-500">User Type:</strong>{" "}
                {isAdmin ? "Admin (A)" : "Regular (U)"}
              </span>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

// Icon components
function UserCircleIcon() {
  return <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
}
function PencilIcon() {
  return <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>;
}
function CardIcon() {
  return <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>;
}
function ListIcon() {
  return <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>;
}
function PlusCircleIcon() {
  return <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
}
function ChartIcon() {
  return <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>;
}
function BankIcon() {
  return <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" /></svg>;
}
function ShieldIcon() {
  return <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>;
}
function UsersIcon() {
  return <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>;
}
function TagIcon() {
  return <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>;
}
