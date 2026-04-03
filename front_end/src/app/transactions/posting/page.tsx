import Link from 'next/link'
import { TransactionPostingForm } from '@/components/forms/TransactionPostingForm'

export default function TransactionPostingPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/" className="hover:text-gray-700">Dashboard</Link>
        <span>/</span>
        <span>Transaction Posting</span>
      </div>
      <TransactionPostingForm />
    </div>
  )
}
