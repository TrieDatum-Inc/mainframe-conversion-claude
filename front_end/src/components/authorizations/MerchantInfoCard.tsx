'use client';

/**
 * MerchantInfoCard — displays merchant details section.
 *
 * Maps COPAU01 rows 17-21:
 *   Row 17: "Merchant Details ---" separator (76-char line)
 *   Row 19: Name (MERNAMEO, BLUE), Merchant ID (MERIDO, BLUE)
 *   Row 21: City (MERCITYO, BLUE), State (MERSTO, BLUE), Zip (MERZIPO, BLUE)
 *
 * All fields are ASKIP (read-only) with BLUE color per COPAU01.bms.
 */

interface MerchantInfoCardProps {
  merchantName: string | null;
  merchantId: string | null;
  merchantCity: string | null;
  merchantState: string | null;
  merchantZip: string | null;
}

export function MerchantInfoCard({
  merchantName,
  merchantId,
  merchantCity,
  merchantState,
  merchantZip,
}: MerchantInfoCardProps) {
  return (
    <div className="mt-6">
      {/* Row 17: Separator line — "Merchant Details ---" */}
      <div className="flex items-center gap-3 mb-4">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">
          Merchant Details
        </h3>
        <div className="flex-1 h-px bg-gray-300" />
      </div>

      {/* Row 19: Name and Merchant ID */}
      <div className="grid grid-cols-2 gap-6 mb-3">
        <div>
          <label className="block text-xs font-medium text-cyan-600 uppercase tracking-wider mb-1">
            Name
          </label>
          <span className="text-sm text-blue-700 font-medium">
            {merchantName ?? '—'}
          </span>
        </div>
        <div>
          <label className="block text-xs font-medium text-cyan-600 uppercase tracking-wider mb-1">
            Merchant ID
          </label>
          <span className="text-sm text-blue-700 font-medium">
            {merchantId ?? '—'}
          </span>
        </div>
      </div>

      {/* Row 21: City, State, Zip */}
      <div className="grid grid-cols-3 gap-6">
        <div>
          <label className="block text-xs font-medium text-cyan-600 uppercase tracking-wider mb-1">
            City
          </label>
          <span className="text-sm text-blue-700 font-medium">
            {merchantCity ?? '—'}
          </span>
        </div>
        <div>
          <label className="block text-xs font-medium text-cyan-600 uppercase tracking-wider mb-1">
            State
          </label>
          <span className="text-sm text-blue-700 font-medium">
            {merchantState ?? '—'}
          </span>
        </div>
        <div>
          <label className="block text-xs font-medium text-cyan-600 uppercase tracking-wider mb-1">
            ZIP
          </label>
          <span className="text-sm text-blue-700 font-medium">
            {merchantZip ?? '—'}
          </span>
        </div>
      </div>
    </div>
  );
}
