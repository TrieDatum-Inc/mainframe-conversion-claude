"use client";

/**
 * Screen header component — mirrors COTRN0A/COTRN1A/COTRN2A header area (Rows 1-2).
 * Fields: TRNNAME, TITLE01, CURDATE, PGMNAME, TITLE02, CURTIME.
 */

interface ScreenHeaderProps {
  tranId: string;
  pgmName: string;
  title: string;
}

export default function ScreenHeader({ tranId, pgmName, title }: ScreenHeaderProps) {
  const now = new Date();
  const dateStr = now.toLocaleDateString("en-US", {
    month: "2-digit",
    day: "2-digit",
    year: "2-digit",
  });
  const timeStr = now.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

  return (
    <div className="bg-gray-950 border-b border-gray-700 px-4 py-2 font-mono text-xs">
      {/* Row 1 */}
      <div className="flex justify-between items-center">
        <span className="text-blue-400">
          Tran: <span className="text-blue-300">{tranId}</span>
        </span>
        <span className="text-yellow-400 font-semibold">{title}</span>
        <span className="text-blue-400">
          Date: <span className="text-blue-300">{dateStr}</span>
        </span>
      </div>
      {/* Row 2 */}
      <div className="flex justify-between items-center mt-0.5">
        <span className="text-blue-400">
          Prog: <span className="text-blue-300">{pgmName}</span>
        </span>
        <span className="text-yellow-400">CardDemo Credit Card Demo Application</span>
        <span className="text-blue-400">
          Time: <span className="text-blue-300">{timeStr}</span>
        </span>
      </div>
    </div>
  );
}
