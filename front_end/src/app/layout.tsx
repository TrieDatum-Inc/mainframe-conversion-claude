import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'CardDemo User Administration',
  description:
    'User Administration module — converted from CardDemo COBOL programs COUSR00C/01C/02C/03C',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-100">
        <nav className="bg-gray-900 text-white px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <span className="text-yellow-400 font-semibold text-sm">
              AWS Mainframe Modernization — CardDemo
            </span>
          </div>
          <span className="text-blue-300 text-xs font-mono">User Administration</span>
        </nav>
        <main className="max-w-6xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
