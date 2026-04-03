"use client";
import { cn } from "@/lib/utils";
interface FKey { label: string; action: () => void; highlighted?: boolean; disabled?: boolean; }
interface FunctionKeyBarProps { keys: FKey[]; }
export function FunctionKeyBar({ keys }: FunctionKeyBarProps) {
  return (
    <div className="bg-gray-900 border-t border-gray-700 px-2 py-1 flex gap-4 font-mono text-sm">
      {keys.map((k) => (
        <button key={k.label} onClick={k.action} disabled={k.disabled}
          className={cn("px-2 py-0.5 rounded transition-colors", k.disabled ? "text-gray-600 cursor-not-allowed" : k.highlighted ? "text-yellow-300 font-bold hover:bg-gray-700" : "text-cyan-300 hover:bg-gray-700")}
          aria-label={k.label}>{k.label}</button>
      ))}
    </div>
  );
}
