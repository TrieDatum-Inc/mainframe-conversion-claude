"use client";
import { useEffect, useState } from "react";
interface ScreenHeaderProps { tranName: string; pgmName: string; title1: string; title2: string; }
function formatDate(d: Date): string { return `${String(d.getMonth()+1).padStart(2,"0")}/${String(d.getDate()).padStart(2,"0")}/${String(d.getFullYear()).slice(2)}`; }
function formatTime(d: Date): string { return `${String(d.getHours()).padStart(2,"0")}:${String(d.getMinutes()).padStart(2,"0")}:${String(d.getSeconds()).padStart(2,"0")}`; }
export function ScreenHeader({ tranName, pgmName, title1, title2 }: ScreenHeaderProps) {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => { setNow(new Date()); const id = setInterval(() => setNow(new Date()), 1000); return () => clearInterval(id); }, []);
  return (
    <div className="bg-gray-900 text-sm font-mono border-b border-gray-700">
      <div className="flex justify-between px-2 py-0.5">
        <div><span className="text-blue-400">Tran: </span><span className="text-blue-300 font-bold">{tranName}</span><span className="mx-6 text-yellow-300">{title1}</span></div>
        <div><span className="text-blue-400">Date: </span><span className="text-blue-300">{now ? formatDate(now) : "--/--/--"}</span></div>
      </div>
      <div className="flex justify-between px-2 py-0.5">
        <div><span className="text-blue-400">Prog: </span><span className="text-blue-300">{pgmName}</span><span className="mx-4 text-yellow-300">{title2}</span></div>
        <div><span className="text-blue-400">Time: </span><span className="text-blue-300">{now ? formatTime(now) : "--:--:--"}</span></div>
      </div>
    </div>
  );
}
