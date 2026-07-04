import clsx from "clsx";
import type { SeatDetail } from "@/types/api";

interface SeatMapProps {
  seats: SeatDetail[];
  selectedSeatIds: Set<number>;
  onToggle: (seat: SeatDetail) => void;
  maxSelectable: number;
}

export function SeatMap({ seats, selectedSeatIds, onToggle, maxSelectable }: SeatMapProps) {
  return (
    <div>
      <div className="mb-4 flex gap-4 text-xs text-slate-600">
        <LegendItem colorClass="bg-white border-slate-300" label="Available" />
        <LegendItem colorClass="bg-brand-600 border-brand-600" label="Selected" />
        <LegendItem colorClass="bg-slate-200 border-slate-200" label="Taken" />
      </div>

      <div className="grid grid-cols-4 gap-3 sm:grid-cols-6">
        {seats.map((seat) => {
          const isSelected = selectedSeatIds.has(seat.id);
          const isAvailable = seat.status === "AVAILABLE";
          const isPickable =
            isSelected || (isAvailable && selectedSeatIds.size < maxSelectable);

          return (
            <button
              key={seat.id}
              type="button"
              disabled={!isAvailable && !isSelected}
              onClick={() => isPickable && onToggle(seat)}
              title={
                !isAvailable
                  ? "Already taken"
                  : !isPickable
                    ? `You can select up to ${maxSelectable} seat(s)`
                    : `Rs. ${seat.price.toLocaleString()}`
              }
              className={clsx(
                "flex h-14 flex-col items-center justify-center rounded-md border text-xs font-medium transition",
                isSelected && "border-brand-600 bg-brand-600 text-white",
                !isSelected && isAvailable && isPickable && "border-slate-300 bg-white text-slate-700 hover:border-brand-500",
                !isSelected && isAvailable && !isPickable && "cursor-not-allowed border-slate-200 bg-slate-50 text-slate-400",
                !isAvailable && "cursor-not-allowed border-slate-200 bg-slate-200 text-slate-400"
              )}
            >
              <span>{seat.seat_number}</span>
              <span className="text-[10px] opacity-80">Rs. {seat.price.toLocaleString()}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function LegendItem({ colorClass, label }: { colorClass: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className={clsx("h-3 w-3 rounded-sm border", colorClass)} />
      {label}
    </div>
  );
}
