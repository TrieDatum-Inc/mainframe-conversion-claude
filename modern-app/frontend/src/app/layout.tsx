import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CardDemo — User Administration",
  description: "Admin portal for CardDemo user management",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
