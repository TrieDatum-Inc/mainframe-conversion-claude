/**
 * Screen header bar — mirrors the top 2 rows of every CardDemo BMS screen:
 * Row 1: Tran: XXXX  <Title01>  Date: MM/DD/YY
 * Row 2: Prog: XXXXXX  <Title02>  Time: HH:MM:SS
 */

"use client";

import { useEffect, useState } from "react";

interface ScreenHeaderProps {
  tranId: string;
  progName: string;
  title01: string;
  title02: string;
}

export function ScreenHeader({ tranId, progName, title01, title02 }: ScreenHeaderProps) {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const dateStr = now
    ? `${String(now.getMonth() + 1).padStart(2, "0")}/${String(now.getDate()).padStart(2, "0")}/${String(now.getFullYear()).slice(-2)}`
    : "";

  const timeStr = now
    ? `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}`
    : "";

  return (
    <div className="bg-blue-900 text-sm font-mono px-2 py-1">
      <div className="flex items-center justify-between">
        <span className="text-blue-300">
          Tran: <span className="text-blue-200 font-semibold">{tranId}</span>
        </span>
        <span className="text-yellow-400 font-semibold flex-1 text-center">{title01}</span>
        <span className="text-blue-300">
          Date: <span className="text-blue-200">{dateStr}</span>
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-blue-300">
          Prog: <span className="text-blue-200 font-semibold">{progName}</span>
        </span>
        <span className="text-yellow-400 font-semibold flex-1 text-center">{title02}</span>
        <span className="text-blue-300">
          Time: <span className="text-blue-200">{timeStr}</span>
        </span>
      </div>
    </div>
  );
}
