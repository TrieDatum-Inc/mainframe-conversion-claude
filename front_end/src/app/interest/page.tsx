import Link from 'next/link'
import { InterestCalculationForm } from '@/components/forms/InterestCalculationForm'

export default function InterestCalculationPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/" className="hover:text-gray-700">Dashboard</Link>
        <span>/</span>
        <span>Interest Calculation</span>
      </div>
      <InterestCalculationForm />
    </div>
  )
}
