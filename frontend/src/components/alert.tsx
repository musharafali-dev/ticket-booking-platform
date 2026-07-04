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
        "rounded-md border px-4 py-3 text-sm",
        variant === "error" && "border-red-200 bg-red-50 text-red-700",
        variant === "success" && "border-green-200 bg-green-50 text-green-700",
        variant === "info" && "border-blue-200 bg-blue-50 text-blue-700"
      )}
    >
      {children}
    </div>
  );
}
