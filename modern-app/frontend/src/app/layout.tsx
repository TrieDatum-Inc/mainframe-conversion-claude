import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CardDemo — Authorization Module",
  description:
    "Card authorization processing and fraud management. Modernized from COBOL CardDemo IMS/MQ/DB2.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased bg-gray-50">{children}</body>
    </html>
  );
}
