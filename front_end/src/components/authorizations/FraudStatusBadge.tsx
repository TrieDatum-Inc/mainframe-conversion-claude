'use client';

/**
 * FraudStatusBadge — color-coded badge for authorization fraud status.
 *
 * Maps COPAU01 AUTHFRDO field (fraud status display):
 *   N → green "No Fraud"        (no AUTHFRDO value on COBOL screen)
 *   F → red "Fraud Confirmed"   (AUTHFRDO = 'FRAUD', RED text)
 *   R → yellow "Fraud Removed"  (AUTHFRDO = 'REMOVED', RED text)
 *
 * BMS attr: AUTHFRDO is ASKIP,NORM,COLOR=RED per COPAU01.bms.
 */

import { FRAUD_STATUS_CONFIG } from '@/types/authorization';

interface FraudStatusBadgeProps {
  status: 'N' | 'F' | 'R';
  /** Show compact version without label text */
  compact?: boolean;
}

export function FraudStatusBadge({
  status,
  compact = false,
}: FraudStatusBadgeProps) {
  const config = FRAUD_STATUS_CONFIG[status];

  if (compact) {
    return (
      <span
        className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ${config.badgeClass}`}
        title={config.label}
      >
        {status}
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-sm font-medium ${config.badgeClass}`}
    >
      {config.label}
    </span>
  );
}
