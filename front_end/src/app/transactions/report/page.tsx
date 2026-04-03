import Link from 'next/link'
import { TransactionReportForm } from '@/components/forms/TransactionReportForm'

export default function TransactionReportPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/" className="hover:text-gray-700">Dashboard</Link>
        <span>/</span>
        <span>Transaction Report</span>
      </div>
      <TransactionReportForm />
    </div>
  )
}
