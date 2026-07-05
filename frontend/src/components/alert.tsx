import clsx from "clsx";

interface AlertProps {
  variant: "error" | "success" | "info";
  children: React.ReactNode;
}

export function Alert({ variant, children }: AlertProps) {
  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      className={clsx(
        "rounded-lg border px-4 py-3.5 text-sm backdrop-blur-md shadow-sm transition-all duration-300",
        variant === "error" && "border-red-500/20 bg-red-500/10 text-red-200 shadow-[0_0_15px_rgba(239,68,68,0.1)]",
        variant === "success" && "border-emerald-500/20 bg-emerald-500/10 text-emerald-200 shadow-[0_0_15px_rgba(16,185,129,0.1)]",
        variant === "info" && "border-blue-500/20 bg-blue-500/10 text-blue-200 shadow-[0_0_15px_rgba(59,130,246,0.1)]"
      )}
    >
      {children}
    </div>
  );
}
