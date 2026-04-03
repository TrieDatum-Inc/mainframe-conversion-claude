import type { Metadata } from "next";
import { Toaster } from "sonner";
import "./globals.css";

export const metadata: Metadata = {
  title: "CardDemo — Account Management",
  description: "CardDemo Account Management — converted from COBOL COACTVWC/COACTUPC",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        <Toaster position="top-right" richColors />
        {children}
      </body>
    </html>
  );
}
