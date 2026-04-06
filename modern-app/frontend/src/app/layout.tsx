import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CardDemo Transaction Manager",
  description: "Modernized CardDemo transaction management portal",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen bg-slate-50`}>
        <nav className="bg-blue-900 text-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold tracking-tight">CardDemo</span>
                <span className="text-blue-300 text-sm font-medium">Transaction Portal</span>
              </div>
              <div className="flex items-center gap-6 text-sm font-medium">
                <Link
                  href="/transactions"
                  className="text-blue-200 hover:text-white transition-colors"
                >
                  Transactions
                </Link>
                <Link
                  href="/transactions/new"
                  className="text-blue-200 hover:text-white transition-colors"
                >
                  Add Transaction
                </Link>
                <Link
                  href="/bill-payment"
                  className="text-blue-200 hover:text-white transition-colors"
                >
                  Bill Payment
                </Link>
                <Link
                  href="/reports"
                  className="text-blue-200 hover:text-white transition-colors"
                >
                  Reports
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">{children}</main>
        <footer className="mt-auto border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
          CardDemo Transaction Module — Modernized from COBOL CICS (COTRN00C, COTRN01C,
          COTRN02C, COBIL00C, CORPT00C)
        </footer>
      </body>
    </html>
  );
}
