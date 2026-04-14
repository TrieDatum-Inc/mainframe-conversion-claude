"use client";

/**
 * AppHeader — standard two-row application header.
 *
 * COBOL origin: BMS header area (rows 1-3 on every map).
 * The original header showed: Tran/Prog/Date/Time/AppID/SysID as fixed-width
 * 3270 terminal fields.
 *
 * Modern equivalent: Clean header bar with title, date/time, and program info.
 * NOT a literal BMS clone — uses contemporary web layout conventions.
 */

import { useEffect, useState } from "react";

interface AppHeaderProps {
  programName: string;
  transactionId: string;
}

function formatDate(date: Date): string {
  // COBOL origin: CURDATEO field format MM/DD/YY
  return date.toLocaleDateString("en-US", {
    month: "2-digit",
    day: "2-digit",
    year: "2-digit",
  });
}

function formatTime(date: Date): string {
  // COBOL origin: CURTIMEO field format HH:MM:SS
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export function AppHeader({ programName, transactionId }: AppHeaderProps) {
  const [currentDate, setCurrentDate] = useState<Date>(new Date());

  // Update clock every second — replaces static CURDATEO/CURTIMEO BMS fields
  useEffect(() => {
    const interval = setInterval(() => setCurrentDate(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-slate-800 text-white px-6 py-3">
      <div className="max-w-5xl mx-auto flex items-center justify-between gap-4">
        {/* Left: program identity */}
        <div className="flex items-center gap-4 text-sm text-slate-300">
          <span>
            <span className="text-slate-500 mr-1">Tran:</span>
            <span className="font-mono">{transactionId}</span>
          </span>
          <span>
            <span className="text-slate-500 mr-1">Prog:</span>
            <span className="font-mono">{programName}</span>
          </span>
        </div>

        {/* Centre: application title */}
        <div className="text-center flex-1">
          <p className="text-yellow-400 font-semibold text-sm tracking-wide">
            CARDDEMO — Credit Card Management System
          </p>
        </div>

        {/* Right: date/time */}
        <div className="flex items-center gap-4 text-sm text-slate-300">
          <span>
            <span className="text-slate-500 mr-1">Date:</span>
            <span className="font-mono">{formatDate(currentDate)}</span>
          </span>
          <span>
            <span className="text-slate-500 mr-1">Time:</span>
            <span className="font-mono">{formatTime(currentDate)}</span>
          </span>
        </div>
      </div>
    </header>
  );
}
