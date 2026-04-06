"use client";

interface StatusBadgeProps {
  status: "Y" | "N" | string;
  activeLabel?: string;
  inactiveLabel?: string;
}

export function StatusBadge({
  status,
  activeLabel = "ACTIVE",
  inactiveLabel = "INACTIVE",
}: StatusBadgeProps) {
  const isActive = status === "Y";
  return (
    <span
      className={`font-mono text-xs px-2 py-0.5 border ${
        isActive
          ? "text-mainframe-success border-mainframe-success"
          : "text-mainframe-error border-mainframe-error"
      }`}
    >
      {isActive ? activeLabel : inactiveLabel}
    </span>
  );
}
