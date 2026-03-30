"use client";

interface AlertMessageProps {
  type: "success" | "error" | "info";
  message: string;
  onDismiss?: () => void;
}

const styles: Record<AlertMessageProps["type"], { bg: string; text: string; border: string }> = {
  success: {
    bg: "bg-green-50",
    text: "text-green-800",
    border: "border-green-300",
  },
  error: {
    bg: "bg-red-50",
    text: "text-red-800",
    border: "border-red-300",
  },
  info: {
    bg: "bg-blue-50",
    text: "text-blue-800",
    border: "border-blue-300",
  },
};

export default function AlertMessage({ type, message, onDismiss }: AlertMessageProps) {
  const s = styles[type];

  return (
    <div
      role="alert"
      className={`flex items-start justify-between rounded-md border px-4 py-3 ${s.bg} ${s.text} ${s.border}`}
    >
      <span className="text-sm leading-5">{message}</span>

      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className={`ml-4 inline-flex flex-shrink-0 rounded p-0.5 hover:opacity-70 focus:outline-none focus:ring-2 focus:ring-offset-1 ${s.text}`}
          aria-label="Dismiss"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}
