import type { Metadata } from "next";
import { Geist_Mono } from "next/font/google";
import "./globals.css";

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CardDemo — AWS Mainframe Modernization",
  description:
    "CardDemo: Mainframe COBOL application converted to modern web stack. Auth & Navigation module (COSGN00C / COMEN01C / COADM01C).",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistMono.variable} h-full`}>
      <body className="min-h-full flex flex-col bg-gray-950 antialiased">
        {children}
      </body>
    </html>
  );
}
