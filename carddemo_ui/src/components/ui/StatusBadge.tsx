"use client";

interface StatusBadgeProps {
  status: string;
  variant?: "dot" | "pill";
}

type ColorSet = { bg: string; text: string; dot: string };

const colorMap: Record<string, ColorSet> = {
  // Green statuses
  Y:        { bg: "bg-green-100", text: "text-green-800", dot: "bg-green-500" },
  Active:   { bg: "bg-green-100", text: "text-green-800", dot: "bg-green-500" },
  Approved: { bg: "bg-green-100", text: "text-green-800", dot: "bg-green-500" },
  "00":     { bg: "bg-green-100", text: "text-green-800", dot: "bg-green-500" },
  // Red statuses
  N:        { bg: "bg-red-100", text: "text-red-800", dot: "bg-red-500" },
  Inactive: { bg: "bg-red-100", text: "text-red-800", dot: "bg-red-500" },
  Declined: { bg: "bg-red-100", text: "text-red-800", dot: "bg-red-500" },
  "05":     { bg: "bg-red-100", text: "text-red-800", dot: "bg-red-500" },
  // Yellow statuses
  P:        { bg: "bg-yellow-100", text: "text-yellow-800", dot: "bg-yellow-500" },
  Pending:  { bg: "bg-yellow-100", text: "text-yellow-800", dot: "bg-yellow-500" },
};

const defaultColor: ColorSet = { bg: "bg-gray-100", text: "text-gray-800", dot: "bg-gray-500" };

export default function StatusBadge({ status, variant = "pill" }: StatusBadgeProps) {
  const colors = colorMap[status] ?? defaultColor;

  if (variant === "dot") {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium">
        <span className={`inline-block h-2 w-2 rounded-full ${colors.dot}`} />
        <span className={colors.text}>{status}</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${colors.bg} ${colors.text}`}
    >
      {status}
    </span>
  );
}
