import clsx from "clsx";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  variant?: "primary" | "secondary" | "danger";
}

export function Button({
  isLoading,
  variant = "primary",
  className,
  disabled,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        "relative overflow-hidden rounded-lg px-5 py-2.5 text-sm font-semibold transition-all duration-300 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-40",
        // Primary variant: Vibrant glow gradient
        variant === "primary" &&
          "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-[0_4px_20px_rgba(37,99,235,0.25)] hover:from-blue-500 hover:to-indigo-500 hover:shadow-[0_4px_25px_rgba(99,102,241,0.4)] hover:-translate-y-[1px]",
        // Secondary variant: Translucent glass panel
        variant === "secondary" &&
          "border border-white/10 bg-white/5 text-slate-200 backdrop-blur-sm hover:bg-white/10 hover:border-white/20 hover:text-white",
        // Danger variant: Glowing red glass
        variant === "danger" &&
          "border border-red-500/30 bg-red-500/10 text-red-300 hover:bg-red-500/20 hover:border-red-500/50 hover:text-white hover:shadow-[0_4px_20px_rgba(239,68,68,0.25)]",
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="flex items-center justify-center gap-2">
          <svg className="h-4 w-4 animate-spin text-current" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Processing...
        </span>
      ) : (
        children
      )}
    </button>
  );
}
