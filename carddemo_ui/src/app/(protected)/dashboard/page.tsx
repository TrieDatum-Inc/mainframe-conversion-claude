"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

interface MenuItem {
  label: string;
  href: string;
  description: string;
}

const userMenuItems: MenuItem[] = [
  { label: "Account View", href: "/accounts/0", description: "View account details by ID" },
  { label: "Credit Card List", href: "/cards", description: "Browse all credit cards" },
  { label: "Credit Card View", href: "/cards", description: "View card details" },
  { label: "Transaction List", href: "/transactions", description: "Browse all transactions" },
  { label: "Add Transaction", href: "/transactions/new", description: "Create a new transaction" },
  { label: "Transaction Reports", href: "/reports", description: "Generate transaction reports" },
  { label: "Bill Payment", href: "/bill-payment", description: "Pay account bills" },
  { label: "Pending Authorizations", href: "/authorizations", description: "View authorization summaries" },
];

const adminMenuItems: MenuItem[] = [
  { label: "User Management", href: "/admin/users", description: "Manage system users" },
  { label: "Add User", href: "/admin/users/new", description: "Create a new user" },
  { label: "Transaction Types", href: "/admin/transaction-types", description: "Manage transaction types" },
  { label: "Add Transaction Type", href: "/admin/transaction-types/new", description: "Create a new transaction type" },
];

export default function DashboardPage() {
  const { user, isAdmin } = useAuth();

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Welcome, {user?.user_id}</h2>
        <p className="mt-1 text-sm text-gray-500">
          CardDemo Credit Card Management System
        </p>
      </div>

      {/* User Menu */}
      <section>
        <h3 className="mb-4 text-lg font-semibold text-gray-800">Operations</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {userMenuItems.map((item) => (
            <Link
              key={item.href + item.label}
              href={item.href}
              className="group rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-all hover:border-brand-300 hover:shadow-md"
            >
              <h4 className="text-sm font-semibold text-gray-900 group-hover:text-brand-700">
                {item.label}
              </h4>
              <p className="mt-1 text-xs text-gray-500">{item.description}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Admin Menu */}
      {isAdmin && (
        <section>
          <h3 className="mb-4 text-lg font-semibold text-gray-800">Administration</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {adminMenuItems.map((item) => (
              <Link
                key={item.href + item.label}
                href={item.href}
                className="group rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-all hover:border-brand-300 hover:shadow-md"
              >
                <h4 className="text-sm font-semibold text-gray-900 group-hover:text-brand-700">
                  {item.label}
                </h4>
                <p className="mt-1 text-xs text-gray-500">{item.description}</p>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
