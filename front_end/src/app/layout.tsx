import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "CardDemo — Transaction Processing",
  description:
    "CardDemo credit card transaction processing — modernized from COBOL CICS programs CT00/CT01/CT02",
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
