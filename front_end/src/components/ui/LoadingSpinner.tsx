"use client";

interface LoadingSpinnerProps {
  readonly message?: string;
}

export function LoadingSpinner({ message = "PROCESSING..." }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div className="text-mainframe-text font-mono text-sm animate-pulse">
        {message}
      </div>
      <div className="mt-2 flex space-x-1">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 bg-mainframe-text rounded-full animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}
