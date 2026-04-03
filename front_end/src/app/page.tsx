import Link from "next/link";

export default function HomePage() {
  return (
    <div className="screen-container p-8">
      {/* BMS header row */}
      <div className="screen-header mb-6">
        <span className="text-blue-400">Tran: <span className="text-blue-300">CT00</span></span>
        <span className="screen-title text-lg">CardDemo — Transaction Processing</span>
        <span className="text-blue-400 text-xs">{new Date().toLocaleDateString()}</span>
      </div>

      <div className="space-y-4 mt-12">
        <h2 className="text-yellow-400 text-center text-xl font-semibold mb-8">
          Transaction Processing Menu
        </h2>

        <div className="grid gap-4 max-w-md mx-auto">
          <Link
            href="/transactions"
            className="btn-primary text-center py-3 text-sm block"
          >
            List Transactions (CT00)
          </Link>
          <Link
            href="/transactions/add"
            className="btn-secondary text-center py-3 text-sm block"
          >
            Add Transaction (CT02)
          </Link>
        </div>
      </div>

      <div className="mt-16 text-center text-xs text-gray-600">
        <p>ENTER=Continue &nbsp; F3=Back</p>
      </div>
    </div>
  );
}
