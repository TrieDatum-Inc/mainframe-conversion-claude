import { cn } from "@/lib/utils";

interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
}

export function Label({ className, required, children, ...props }: LabelProps) {
  return (
    <label
      className={cn("block text-sm font-medium text-cyan-700", className)}
      {...props}
    >
      {children}
      {required && <span className="ml-1 text-red-500">*</span>}
    </label>
  );
}
