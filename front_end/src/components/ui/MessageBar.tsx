"use client";

type MessageType = "error" | "success" | "info" | "warn";

interface MessageBarProps {
  readonly type: MessageType;
  readonly message: string;
  readonly onDismiss?: () => void;
}

const colorMap: Record<MessageType, string> = {
  error: "text-mainframe-error border-mainframe-error",
  success: "text-mainframe-success border-mainframe-success",
  info: "text-mainframe-info border-mainframe-info",
  warn: "text-mainframe-warn border-mainframe-warn",
};

const prefixMap: Record<MessageType, string> = {
  error: "** ERROR **",
  success: "** OK **",
  info: "** INFO **",
  warn: "** WARN **",
};

export function MessageBar({ type, message, onDismiss }: MessageBarProps) {
  return (
    <div
      className={`font-mono text-sm border px-3 py-2 flex items-center justify-between ${colorMap[type]}`}
    >
      <span>
        <span className="font-bold mr-2">{prefixMap[type]}</span>
        {message}
      </span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="ml-4 text-xs underline hover:opacity-75"
          aria-label="Dismiss"
        >
          [X]
        </button>
      )}
    </div>
  );
}
