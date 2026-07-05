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
      {/* Legend */}
      <div className="mb-6 flex gap-5 text-xs font-semibold text-slate-400 border-b border-white/5 pb-4">
        <LegendItem colorClass="bg-white/5 border-white/15" label="Available" />
        <LegendItem colorClass="bg-emerald-500/20 border-emerald-500/50 text-emerald-400" label="Selected" />
        <LegendItem colorClass="bg-slate-950/80 border-white/5 text-slate-600" label="Taken" />
      </div>

      {/* Seat Grid */}
      <div className="grid grid-cols-4 gap-3.5 sm:grid-cols-6 md:grid-cols-8">
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
                "flex h-14 flex-col items-center justify-center rounded-xl border text-xs font-bold transition-all duration-300 relative overflow-hidden",
                // Selected seat state
                isSelected &&
                  "border-emerald-500 bg-emerald-500/20 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)] scale-[1.02]",
                // Available and Pickable seat state
                !isSelected &&
                  isAvailable &&
                  isPickable &&
                  "border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 hover:border-blue-500/50 hover:shadow-[0_0_12px_rgba(59,130,246,0.15)] hover:scale-[1.03]",
                // Available but not Pickable (reached max seats)
                !isSelected &&
                  isAvailable &&
                  !isPickable &&
                  "cursor-not-allowed border-white/5 bg-white/[0.02] text-slate-500",
                // Taken seat state
                !isAvailable &&
                  "cursor-not-allowed border-white/5 bg-slate-950/80 text-slate-600"
              )}
            >
              <span className="z-10">{seat.seat_number}</span>
              <span className="text-[9px] font-medium opacity-70 z-10">
                Rs. {seat.price.toLocaleString()}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function LegendItem({ colorClass, label }: { colorClass: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className={clsx("h-3.5 w-3.5 rounded-md border backdrop-blur-sm", colorClass)} />
      <span>{label}</span>
    </div>
  );
}
