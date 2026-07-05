import { forwardRef } from "react";
import clsx from "clsx";

interface TextFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const fieldId = id ?? props.name;
    return (
      <div className="flex flex-col gap-1.5 w-full">
        <label htmlFor={fieldId} className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {label}
        </label>
        <input
          ref={ref}
          id={fieldId}
          className={clsx(
            "glass-input w-full rounded-lg px-3.5 py-2.5 text-sm transition-all duration-200 outline-none",
            error ? "border-red-500/40 focus:border-red-500 focus:shadow-[0_0_15px_rgba(239,68,68,0.2)]" : "border-white/10 hover:border-white/20 focus:border-blue-500 focus:shadow-[0_0_15px_rgba(59,130,246,0.25)]",
            className
          )}
          aria-invalid={!!error}
          aria-describedby={error ? `${fieldId}-error` : undefined}
          {...props}
        />
        {error && (
          <p id={`${fieldId}-error`} className="text-xs text-red-400 font-medium">
            {error}
          </p>
        )}
      </div>
    );
  }
);
TextField.displayName = "TextField";
