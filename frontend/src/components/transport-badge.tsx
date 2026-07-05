import type { TransportType } from "@/types/api";
import clsx from "clsx";

const LABELS: Record<TransportType, string> = {
  BUS: "🚌 Bus",
  TRAIN: "🚆 Train",
  AIRPLANE: "✈️ Flight",
};

const STYLES: Record<TransportType, string> = {
  BUS: "bg-amber-500/10 text-amber-300 border-amber-500/25 shadow-[0_0_10px_rgba(245,158,11,0.05)]",
  TRAIN: "bg-purple-500/10 text-purple-300 border-purple-500/25 shadow-[0_0_10px_rgba(168,85,247,0.05)]",
  AIRPLANE: "bg-sky-500/10 text-sky-300 border-sky-500/25 shadow-[0_0_10px_rgba(56,189,248,0.05)]",
};

export function TransportBadge({ type }: { type: TransportType }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold backdrop-blur-sm transition-all duration-300",
        STYLES[type]
      )}
    >
      {LABELS[type]}
    </span>
  );
}
