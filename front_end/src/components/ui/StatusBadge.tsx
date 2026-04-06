/**
 * StatusBadge component.
 *
 * COBOL origin: Maps ACSTTUS (account status) and CRDSTCD (card status) Y/N display.
 * In the BMS maps these were ASKIP text fields; here rendered as colored badges.
 */

'use client';

interface StatusBadgeProps {
  /** Y or N value */
  status: string;
  /** Label for active state (default: 'Active') */
  activeLabel?: string;
  /** Label for inactive state (default: 'Inactive') */
  inactiveLabel?: string;
}

export default function StatusBadge({
  status,
  activeLabel = 'Active',
  inactiveLabel = 'Inactive',
}: StatusBadgeProps) {
  const isActive = status === 'Y';

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        isActive
          ? 'bg-green-100 text-green-800'
          : 'bg-red-100 text-red-800'
      }`}
    >
      {isActive ? activeLabel : inactiveLabel}
    </span>
  );
}
