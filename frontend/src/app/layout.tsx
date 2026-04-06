/**
 * Root layout for the CardDemo Next.js application.
 *
 * Wraps all pages with global providers:
 * - HTML/body structure with global CSS
 * - The Zustand auth store is initialized client-side via the
 *   'use client' directive in the store itself
 *
 * COBOL origin: No direct equivalent. In CICS, each program managed its
 * own screen independently. This layout provides the consistent application
 * shell that wraps all pages.
 */

import type { Metadata } from 'next';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: 'CardDemo — Credit Card Management',
  description:
    'Modernized CardDemo mainframe application. AWS Mainframe Cloud Demo — Credit Card Demo.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
