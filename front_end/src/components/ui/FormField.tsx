"use client";
import { forwardRef } from "react";
import { cn } from "@/lib/utils";
interface FormFieldProps extends React.InputHTMLAttributes<HTMLInputElement> { label: string; error?: string; protected?: boolean; hint?: string; }
export const FormField = forwardRef<HTMLInputElement, FormFieldProps>(({ label, error, protected: isProtected, hint, className, ...props }, ref) => (
  <div className="flex items-center gap-2 font-mono text-sm">
    <label htmlFor={props.id} className="text-cyan-300 w-52 shrink-0 text-right">{label} :</label>
    {isProtected ? (
      <span className="text-white border-b border-gray-600 min-w-32 px-1 py-0.5 bg-gray-800" aria-readonly="true">{String(props.value ?? "")}</span>
    ) : (
      <input ref={ref} className={cn("bg-gray-900 text-green-300 border-b border-green-500 underline focus:outline-none focus:border-green-300 px-1 py-0.5", error && "border-red-500 text-red-300", className)} aria-invalid={Boolean(error)} aria-describedby={error ? `${props.id}-error` : undefined} {...props} />
    )}
    {hint && <span className="text-blue-400 text-xs">{hint}</span>}
    {error && <span id={`${props.id}-error`} className="text-red-400 text-xs ml-1" role="alert">{error}</span>}
  </div>
));
FormField.displayName = "FormField";
