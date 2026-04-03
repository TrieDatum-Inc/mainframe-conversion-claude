import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "CardDemo - Credit Card Management", description: "AWS CardDemo mainframe modernisation" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="en"><body className="bg-gray-950 text-white">{children}</body></html>);
}
