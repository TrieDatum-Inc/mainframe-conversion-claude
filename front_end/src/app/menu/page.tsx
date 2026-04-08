"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { AppHeader } from "@/components/layout/AppHeader";

interface MenuOption {
  key: string;
  label: string;
  description: string;
  href: string;
}

const MENU_OPTIONS: MenuOption[] = [
  {
    key: "1",
    label: "ACCOUNT VIEW",
    description: "View account details and linked customer (COACTVWC)",
    href: "/accounts/view",
  },
  {
    key: "2",
    label: "ACCOUNT UPDATE",
    description: "Update account status and customer details (COACTUPC)",
    href: "/accounts/update",
  },
  {
    key: "3",
    label: "CARD LIST",
    description: "Browse credit cards by account (COCRDLIC)",
    href: "/cards/list",
  },
  {
    key: "4",
    label: "CARD VIEW",
    description: "View credit card details (COCRDSLC)",
    href: "/cards/view",
  },
  {
    key: "5",
    label: "CARD UPDATE",
    description: "Update credit card embossed name and expiry (COCRDUPC)",
    href: "/cards/update",
  },
];

/**
 * Main menu page.
 * Equivalent to COMEN01C (CICS main menu program).
 */
export default function MenuPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null; // Prevent flash before redirect fires
  }

  return (
    <div className="min-h-screen bg-mainframe-bg">
      <AppHeader
        title="CREDIT CARD DEMO - MAIN MENU"
        subtitle="AWS MAINFRAME MODERNIZATION"
      />

      <main className="container mx-auto px-4 py-8 max-w-3xl">
        <div className="border border-mainframe-border p-6">
          <p className="text-mainframe-dim text-xs mb-6">
            SELECT OPTION AND PRESS ENTER, OR PRESS PF3 TO EXIT
          </p>

          <div className="space-y-3">
            {MENU_OPTIONS.map((option) => (
              <div
                key={option.key}
                role="button"
                tabIndex={0}
                className="flex items-start space-x-4 group cursor-pointer hover:bg-mainframe-panel p-2 transition-colors"
                onClick={() => router.push(option.href)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    router.push(option.href);
                  }
                }}
              >
                <span className="text-mainframe-info font-bold text-sm w-4">
                  {option.key}.
                </span>
                <div>
                  <span className="text-mainframe-text text-sm font-bold group-hover:text-mainframe-info">
                    {option.label}
                  </span>
                  <p className="text-mainframe-dim text-xs mt-0.5">
                    {option.description}
                  </p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 border-t border-mainframe-border pt-4">
            <div className="flex justify-between text-xs text-mainframe-dim">
              <span>PF3=EXIT (LOGOFF)</span>
              <span>ENTER=SELECT</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
