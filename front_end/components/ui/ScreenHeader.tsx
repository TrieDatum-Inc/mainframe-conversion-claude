/**
 * ScreenHeader component — maps COBOL POPULATE-HEADER-INFO paragraph.
 *
 * Renders the standard 2-row header present on ALL CardDemo BMS screens:
 *   Row 1: Tran: [TRNNAME]    [TITLE01 (40 chars)]    Date: [CURDATE]
 *   Row 2: Prog: [PGMNAME]    [TITLE02 (40 chars)]    Time: [CURTIME]
 *
 * BMS field color mappings:
 *   Static labels ("Tran:", "Prog:", etc.) → text-blue-600 (DFHBLUE)
 *   TITLE01 / TITLE02 → text-yellow-600 (DFHYELLOW)
 *   Date / Time values → text-blue-600 (DFHBLUE)
 */
import { formatHeaderDate, formatHeaderTime } from "@/lib/utils";

interface ScreenHeaderProps {
  /** TRNNAMEO — transaction ID displayed in header (CC00 / CM00 / CA00) */
  transactionId: string;
  /** PGMNAMEO — program name (COSGN00C / COMEN01C / COADM01C) */
  programName: string;
  /** TITLE01O — application title line 1 */
  title01?: string;
  /** TITLE02O — application title line 2 */
  title02?: string;
  /** ISO datetime string for CURDATEO / CURTIMEO */
  serverTime?: string;
}

export function ScreenHeader({
  transactionId,
  programName,
  title01 = "AWS Mainframe Modernization",
  title02 = "CardDemo",
  serverTime,
}: ScreenHeaderProps) {
  const now = serverTime ?? new Date().toISOString();
  const dateDisplay = formatHeaderDate(now);
  const timeDisplay = formatHeaderTime(now);

  return (
    <div className="bg-gray-900 text-sm font-mono border-b border-gray-700">
      {/* Row 1: Tran + Title01 + Date */}
      <div className="flex items-center px-4 py-1 gap-2">
        <span className="text-blue-400 w-12">Tran:</span>
        <span className="text-blue-300 w-16">{transactionId}</span>
        <span className="text-yellow-400 flex-1 text-center tracking-wide">
          {title01}
        </span>
        <span className="text-blue-400">Date:</span>
        <span className="text-blue-300 w-20 text-right">{dateDisplay}</span>
      </div>

      {/* Row 2: Prog + Title02 + Time */}
      <div className="flex items-center px-4 py-1 gap-2">
        <span className="text-blue-400 w-12">Prog:</span>
        <span className="text-blue-300 w-16">{programName}</span>
        <span className="text-yellow-400 flex-1 text-center tracking-wide">
          {title02}
        </span>
        <span className="text-blue-400">Time:</span>
        <span className="text-blue-300 w-20 text-right">{timeDisplay}</span>
      </div>
    </div>
  );
}
