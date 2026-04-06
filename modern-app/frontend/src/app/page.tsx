import Link from "next/link";

export default function HomePage() {
  const modules = [
    {
      title: "Transaction List",
      description:
        "Browse and search all transactions. Filter by date, card number, or transaction ID.",
      href: "/transactions",
      cobol: "CT00 / COTRN00C",
      icon: "List",
    },
    {
      title: "Add Transaction",
      description:
        "Create a new transaction record. Enter account or card number and transaction details.",
      href: "/transactions/new",
      cobol: "CT02 / COTRN02C",
      icon: "Plus",
    },
    {
      title: "Bill Payment",
      description:
        "Pay the full outstanding balance for an account. Requires confirmation before processing.",
      href: "/bill-payment",
      cobol: "CB00 / COBIL00C",
      icon: "CreditCard",
    },
    {
      title: "Transaction Reports",
      description:
        "Generate monthly, yearly, or custom date-range transaction reports.",
      href: "/reports",
      cobol: "CR00 / CORPT00C",
      icon: "FileText",
    },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Transaction Management</h1>
        <p className="mt-2 text-slate-600">
          Modernized CardDemo transaction portal — converted from COBOL CICS mainframe application.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {modules.map((mod) => (
          <Link
            key={mod.href}
            href={mod.href}
            className="group block rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md hover:border-blue-300 transition-all"
          >
            <div className="flex items-start justify-between">
              <h2 className="text-lg font-semibold text-slate-900 group-hover:text-blue-700 transition-colors">
                {mod.title}
              </h2>
              <span className="text-xs font-mono bg-slate-100 text-slate-500 px-2 py-1 rounded">
                {mod.cobol}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-600">{mod.description}</p>
            <div className="mt-4 text-sm font-medium text-blue-600 group-hover:text-blue-800">
              Open &rarr;
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
