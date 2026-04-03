"use client";
import { cn } from "@/lib/utils";
interface MessageBarProps { message: string | null; type?: "error" | "info" | "success"; className?: string; }
export function MessageBar({ message, type = "info", className }: MessageBarProps) {
  if (!message) return null;
  const styles = { error: "bg-gray-900 text-red-400 border border-red-600 font-bold", info: "bg-gray-900 text-gray-300 border border-gray-600", success: "bg-gray-900 text-green-400 border border-green-600" };
  return <div className={cn("font-mono text-sm px-3 py-1.5 rounded", styles[type], className)} role={type === "error" ? "alert" : "status"} aria-live={type === "error" ? "assertive" : "polite"}>{message}</div>;
}
