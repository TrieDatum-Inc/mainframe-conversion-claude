/**
 * AppHeader — maps to the standard BMS header (rows 1–3 on every map).
 *
 * COBOL origin: POPULATE-HEADER-INFO paragraph in every CICS program:
 *   MOVE 'COSGN00C' TO PGMNAMEO
 *   MOVE WS-TRANID  TO TRNNAMEO
 *   MOVE WS-DATE    TO CURDATEO
 *   MOVE WS-TIME    TO CURTIMEO
 *   MOVE CCDA-TITLE01 TO TITLE01O
 *   MOVE CCDA-TITLE02 TO TITLE02O
 *
 * BMS field mapping:
 *   TITLE01O (YELLOW, col 21-60) → title line 1 (centered, yellow)
 *   TITLE02O (YELLOW, col 21-60) → title line 2 (centered, yellow)
 *   TRNNAMEO (BLUE, col 8-11)   → transaction ID
 *   PGMNAMEO (BLUE, col 8-15)   → program name
 *   CURDATEO (BLUE, col 71-78)  → current date (MM/DD/YY)
 *   CURTIMEO (BLUE, col 71-79)  → current time (HH:MM:SS)
 */

'use client';

import { useEffect, useState } from 'react';

interface AppHeaderProps {
  programName: string;   // PGMNAMEO — e.g. 'COSGN00C'
  transactionId: string; // TRNNAMEO — e.g. 'CC00'
}

export function AppHeader({ programName, transactionId }: AppHeaderProps) {
  const [currentDate, setCurrentDate] = useState('');
  const [currentTime, setCurrentTime] = useState('');

  useEffect(() => {
    // Initialize date/time
    const update = () => {
      const now = new Date();
      // MM/DD/YY format — matches CURDATEO BMS field format
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const year = String(now.getFullYear()).slice(-2);
      setCurrentDate(`${month}/${day}/${year}`);

      // HH:MM:SS format — matches CURTIMEO BMS field format
      const hours = String(now.getHours()).padStart(2, '0');
      const mins = String(now.getMinutes()).padStart(2, '0');
      const secs = String(now.getSeconds()).padStart(2, '0');
      setCurrentTime(`${hours}:${mins}:${secs}`);
    };

    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-gray-900 text-sm border-b border-gray-700">
      {/* Row 1: Tran / Title01 / Date */}
      <div className="flex items-center justify-between px-4 py-1 font-mono">
        <div className="flex items-center gap-2">
          <span className="text-blue-400">Tran :</span>
          <span className="text-blue-300 font-semibold">{transactionId}</span>
        </div>
        <div className="text-yellow-400 font-bold text-center flex-1 px-4">
          AWS Mainframe Cloud Demo
        </div>
        <div className="flex items-center gap-2">
          <span className="text-blue-400">Date :</span>
          <span className="text-blue-300">{currentDate}</span>
        </div>
      </div>

      {/* Row 2: Prog / Title02 / Time */}
      <div className="flex items-center justify-between px-4 py-1 font-mono">
        <div className="flex items-center gap-2">
          <span className="text-blue-400">Prog :</span>
          <span className="text-blue-300">{programName}</span>
        </div>
        <div className="text-yellow-400 font-bold text-center flex-1 px-4">
          Credit Card Demo Application
        </div>
        <div className="flex items-center gap-2">
          <span className="text-blue-400">Time :</span>
          <span className="text-blue-300">{currentTime}</span>
        </div>
      </div>
    </header>
  );
}
