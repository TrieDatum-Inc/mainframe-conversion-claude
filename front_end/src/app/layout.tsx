import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "CardDemo - AWS Mainframe Modernization",
  description: "Credit Card Management System - Modernized from COBOL/CICS",
};

export default function RootLayout({
  children,
}: {
  readonly children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-mainframe-bg text-mainframe-text font-mono antialiased">
        {children}
      </body>
    </html>
  );
}
