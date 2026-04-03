/**
 * Error message banner — mirrors ERRMSG field (row 23) in all COTRN screens.
 * ATTRB=(ASKIP,BRT,FSET) RED color.
 */
interface ErrorMessageProps {
  message: string | null;
  variant?: "error" | "success" | "info";
}

export default function ErrorMessage({ message, variant = "error" }: ErrorMessageProps) {
  if (!message) return null;

  const styles = {
    error: "text-red-400 bg-red-950 border-red-800",
    success: "text-green-400 bg-green-950 border-green-800",
    info: "text-blue-400 bg-blue-950 border-blue-800",
  };

  return (
    <div
      className={`text-xs font-medium border px-3 py-2 rounded font-mono ${styles[variant]}`}
      role="alert"
      aria-live="polite"
    >
      {message}
    </div>
  );
}
