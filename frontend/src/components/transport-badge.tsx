import type { TransportType } from "@/types/api";
import clsx from "clsx";

const LABELS: Record<TransportType, string> = {
  BUS: "🚌 Bus",
  TRAIN: "🚂 Train",
  AIRPLANE: "✈️ Flight",
};

const STYLES: Record<TransportType, string> = {
  BUS: "bg-amber-50 text-amber-700",
  TRAIN: "bg-purple-50 text-purple-700",
  AIRPLANE: "bg-sky-50 text-sky-700",
};

export function TransportBadge({ type }: { type: TransportType }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        STYLES[type]
      )}
    >
      {LABELS[type]}
    </span>
  );
}
