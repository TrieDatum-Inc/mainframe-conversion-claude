"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

interface NavItem {
  label: string;
  href: string;
  icon: string;
  description?: string;
}

const userNavItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: "\u{1F4CA}" },
  {
    label: "Account View",
    href: "/accounts/0",
    icon: "\u{1F4C2}",
    description: "Enter an account ID to view details",
  },
  { label: "Cards", href: "/cards", icon: "\u{1F4B3}" },
  { label: "Transactions", href: "/transactions", icon: "\u{1F4C4}" },
  { label: "Authorizations", href: "/authorizations", icon: "\u2705" },
  { label: "Bill Payment", href: "/bill-payment", icon: "\u{1F4B0}" },
  { label: "Reports", href: "/reports", icon: "\u{1F4C8}" },
];

const adminNavItems: NavItem[] = [
  { label: "User Management", href: "/admin/users", icon: "\u{1F465}" },
  {
    label: "Transaction Types",
    href: "/admin/transaction-types",
    icon: "\u{1F3F7}\uFE0F",
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { isAdmin } = useAuth();

  const isActive = (href: string): boolean => {
    if (href === "/dashboard") {
      return pathname === href;
    }
    return pathname === href || pathname.startsWith(href + "/");
  };

  return (
    <aside className="flex w-64 flex-col border-r border-gray-200 bg-white">
      <nav className="flex-1 overflow-y-auto py-4">
        {/* All Users Section */}
        <ul className="space-y-1 px-3">
          {userNavItems.map((item) => {
            const active = isActive(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    active
                      ? "bg-brand-100 text-brand-700"
                      : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                  }`}
                >
                  <span className="text-base leading-none">{item.icon}</span>
                  <div className="flex flex-col">
                    <span>{item.label}</span>
                    {item.description && (
                      <span className="text-xs font-normal text-gray-400">
                        {item.description}
                      </span>
                    )}
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>

        {/* Admin Section */}
        {isAdmin && (
          <>
            <div className="mx-3 my-4 border-t border-gray-200" />
            <div className="px-6 pb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                Administration
              </span>
            </div>
            <ul className="space-y-1 px-3">
              {adminNavItems.map((item) => {
                const active = isActive(item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                        active
                          ? "bg-brand-100 text-brand-700"
                          : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                      }`}
                    >
                      <span className="text-base leading-none">
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </>
        )}
      </nav>
    </aside>
  );
}
