import Link from "next/link";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          CardDemo Authorization Module
        </h1>
        <p className="text-sm text-gray-500 mb-8">
          Modernized from COBOL IMS/DB2/MQ Authorization Sub-Application
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/authorizations"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            View Authorizations (CPVS)
          </Link>
          <Link
            href="/authorizations/process"
            className="px-6 py-3 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors text-sm font-medium"
          >
            Process Authorization (CP00)
          </Link>
        </div>
      </div>
    </div>
  );
}
