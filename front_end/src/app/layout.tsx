import type { Metadata } from 'next'
import '@/styles/globals.css'

export const metadata: Metadata = {
  title: 'CardDemo Batch Processing',
  description: 'Modernized COBOL batch processing module — CBTRN02C, CBTRN03C, CBACT04C, CBEXPORT, CBIMPORT',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  CardDemo Batch Processing
                </h1>
                <p className="text-xs text-gray-500 mt-0.5">
                  Modernized from COBOL/VSAM — CBTRN02C | CBTRN03C | CBACT04C | CBEXPORT | CBIMPORT
                </p>
              </div>
              <span className="badge text-green-700 bg-green-50 border-green-200">
                Modern Stack
              </span>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">
          {children}
        </main>
        <footer className="border-t border-gray-200 mt-12">
          <div className="max-w-7xl mx-auto px-4 py-4 text-xs text-gray-400 text-center">
            CardDemo v2.0 — Converted from IBM COBOL/CICS/VSAM to FastAPI/PostgreSQL/Next.js
          </div>
        </footer>
      </body>
    </html>
  )
}
