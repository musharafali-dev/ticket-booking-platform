import type { TransportType } from "@/types/api";
import clsx from "clsx";

const LABELS: Record<TransportType, string> = {
  BUS: "Bus",
  TRAIN: "Train",
  AIRPLANE: "Flight",
};

const STYLES: Record<TransportType, string> = {
  BUS: "bg-amber-500/10 text-amber-300 border-amber-500/25 shadow-[0_0_10px_rgba(245,158,11,0.05)]",
  TRAIN: "bg-purple-500/10 text-purple-300 border-purple-500/25 shadow-[0_0_10px_rgba(168,85,247,0.05)]",
  AIRPLANE: "bg-sky-500/10 text-sky-300 border-sky-500/25 shadow-[0_0_10px_rgba(56,189,248,0.05)]",
};

function getIcon(type: TransportType) {
  if (type === "BUS") {
    return (
      <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 18.75a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0ZM7.5 18.75a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0ZM2.25 15h19.5M3 18.75h18M4.5 5.25h15a2.25 2.25 0 0 1 2.25 2.25v7.5a2.25 2.25 0 0 1-2.25 2.25h-15A2.25 2.25 0 0 1 2.25 15v-7.5A2.25 2.25 0 0 1 4.5 5.25Zm0 4.5h15v-1.5h-15v1.5Zm0 3.75h15v-1.5h-15v1.5Z" />
      </svg>
    );
  }
  if (type === "TRAIN") {
    return (
      <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5.25 19.5h13.5M5.25 4.5h13.5m-10.5 3h7.5m-7.5 3h7.5m-7.5 3h7.5M5.25 4.5A2.25 2.25 0 0 0 3 6.75v10.5A2.25 2.25 0 0 0 5.25 19.5M18.75 4.5A2.25 2.25 0 0 1 21 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25M6 19.5l-1.5 3m13.5-3 1.5 3" />
      </svg>
    );
  }
  return (
    <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L6 12Zm0 0h7.5" />
    </svg>
  );
}

export function TransportBadge({ type }: { type: TransportType }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold backdrop-blur-sm transition-all duration-300",
        STYLES[type]
      )}
    >
      {getIcon(type)}
      <span>{LABELS[type]}</span>
    </span>
  );
}
