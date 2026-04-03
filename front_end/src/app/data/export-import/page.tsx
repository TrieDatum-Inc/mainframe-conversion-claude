import Link from 'next/link'
import { ExportImportPanel } from '@/components/forms/ExportImportPanel'

export default function ExportImportPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/" className="hover:text-gray-700">Dashboard</Link>
        <span>/</span>
        <span>Export / Import</span>
      </div>
      <ExportImportPanel />
    </div>
  )
}
