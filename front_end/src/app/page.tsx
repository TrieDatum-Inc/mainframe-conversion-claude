import Link from 'next/link'

/**
 * Dashboard — lists all batch processing operations converted from COBOL.
 */

const modules = [
  {
    href: '/transactions/posting',
    title: 'Transaction Posting',
    cobolProgram: 'CBTRN02C',
    description: 'Validate and post daily transactions. Returns rejects with reason codes.',
    details: [
      'Reason 100: Invalid card number',
      'Reason 101: Account not found',
      'Reason 102: Over credit limit',
      'Reason 103: Account expired (overwrites 102)',
    ],
    color: 'blue',
  },
  {
    href: '/transactions/report',
    title: 'Transaction Report',
    cobolProgram: 'CBTRN03C',
    description: 'Generate DALYREPT transaction detail report for a date range.',
    details: [
      'Date range filter (DATEPARM equivalent)',
      'Account break subtotals',
      'Page breaks every 20 lines',
      'Grand total at end',
    ],
    color: 'purple',
  },
  {
    href: '/interest',
    title: 'Interest Calculation',
    cobolProgram: 'CBACT04C',
    description: 'Calculate and post monthly interest charges for all accounts.',
    details: [
      'Formula: (balance × rate) / 1200',
      'DEFAULT group fallback',
      'Cycle credit/debit zeroed',
      'Fee calc (stub) — TODO',
    ],
    color: 'green',
  },
  {
    href: '/data/export-import',
    title: 'Data Export / Import',
    cobolProgram: 'CBEXPORT / CBIMPORT',
    description: 'Export all entities to JSON, then import back with validation.',
    details: [
      'C/A/X/T/D record type routing',
      'Referential integrity validation',
      'Upsert on re-import',
      'Download export as JSON',
    ],
    color: 'orange',
  },
]

const colorClasses: Record<string, string> = {
  blue: 'border-blue-200 hover:border-blue-400 bg-blue-50',
  purple: 'border-purple-200 hover:border-purple-400 bg-purple-50',
  green: 'border-green-200 hover:border-green-400 bg-green-50',
  orange: 'border-orange-200 hover:border-orange-400 bg-orange-50',
}

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Batch Processing Operations</h2>
        <p className="text-gray-500 mt-1">
          Converted from IBM COBOL batch programs running under JCL/VSAM on z/OS mainframe.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {modules.map((mod) => (
          <Link key={mod.href} href={mod.href}>
            <div
              className={`card p-6 border-2 transition-all duration-200 hover:shadow-md cursor-pointer ${
                colorClasses[mod.color]
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900">{mod.title}</h3>
                <span className="text-xs font-mono bg-white border border-gray-200 px-2 py-0.5 rounded text-gray-600">
                  {mod.cobolProgram}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-3">{mod.description}</p>
              <ul className="space-y-1">
                {mod.details.map((d) => (
                  <li key={d} className="text-xs text-gray-500 flex items-start gap-1">
                    <span className="text-gray-400 mt-0.5">•</span>
                    {d}
                  </li>
                ))}
              </ul>
            </div>
          </Link>
        ))}
      </div>

      {/* Architecture note */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
        <p className="font-medium text-gray-900 mb-2">Mainframe-to-Modern Architecture Mapping</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div>
            <p className="font-medium text-gray-700">Storage</p>
            <p>VSAM KSDS → PostgreSQL tables</p>
            <p>GDG output files → DB audit tables</p>
            <p>Sequential flat files → JSON API responses</p>
          </div>
          <div>
            <p className="font-medium text-gray-700">Processing</p>
            <p>JCL batch jobs → REST API endpoints</p>
            <p>PERFORM paragraphs → Service methods</p>
            <p>File status codes → HTTP status codes</p>
          </div>
          <div>
            <p className="font-medium text-gray-700">Error Handling</p>
            <p>CEE3ABD ABEND → HTTP 500 + logging</p>
            <p>RETURN-CODE 4 → has_rejects=true</p>
            <p>IO-STATUS → Exception classes</p>
          </div>
        </div>
      </div>
    </div>
  )
}
