"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useScheduleDetail } from "@/hooks/use-schedule-detail";
import { useBookingFlowStore } from "@/store/booking-flow-store";
import { SeatMap } from "@/components/seat-map";
import { Button } from "@/components/button";
import { Alert } from "@/components/alert";
import { TransportBadge } from "@/components/transport-badge";

const MAX_PASSENGERS = 6;

function BookingSteps({ currentStep }: { currentStep: 1 | 2 | 3 }) {
  return (
    <div className="flex items-center justify-center gap-3 mb-6 text-[10px] sm:text-xs font-bold uppercase tracking-wider">
      <span className={currentStep === 1 ? "text-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.2)]" : "text-slate-500"}>
        1. Select Seats
      </span>
      <span className="text-slate-600">➔</span>
      <span className={currentStep === 2 ? "text-blue-400" : "text-slate-500"}>
        2. Passengers Info
      </span>
      <span className="text-slate-600">➔</span>
      <span className={currentStep === 3 ? "text-blue-400" : "text-slate-500"}>
        3. Payment Checkout
      </span>
    </div>
  );
}

export default function SeatSelectionPage() {
  const params = useParams<{ scheduleId: string }>();
  const scheduleId = Number(params.scheduleId);
  const router = useRouter();

  const selectedSeats = useBookingFlowStore((s) => s.selectedSeats);
  const toggleSeat = useBookingFlowStore((s) => s.toggleSeat);

  const [passengerCount, setPassengerCount] = useState(1);

  const { data: detail, error, isLoading } = useScheduleDetail(
    Number.isFinite(scheduleId) ? scheduleId : null
  );

  useEffect(() => {
    if (selectedSeats.length > passengerCount) {
      const excess = selectedSeats.slice(passengerCount);
      excess.forEach((s) => toggleSeat(s));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [passengerCount]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20" role="status">
        <svg className="h-8 w-8 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p className="text-slate-400 font-medium">Loading layout matrix...</p>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <Alert variant="error">
        Could not load this schedule. It may no longer be available.{" "}
        <button onClick={() => router.push("/")} className="underline font-bold text-white ml-1">
          Back to search
        </button>
      </Alert>
    );
  }

  const selectedIds = new Set(selectedSeats.map((s) => s.id));
  const totalPrice = selectedSeats.reduce((sum, s) => sum + s.price, 0);

  const handleContinue = () => {
    router.push(`/schedules/${scheduleId}/passengers`);
  };

  return (
    <div className="flex flex-col gap-6 max-w-2xl mx-auto">
      {/* Step Indicator */}
      <BookingSteps currentStep={1} />

      {/* Operator Header Card */}
      <div className="glass-panel rounded-xl p-5 border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="mb-2.5 flex items-center gap-2.5">
            <TransportBadge type={detail.operator.operator_type} />
            <h1 className="text-xl font-extrabold text-white">{detail.operator.operator_name}</h1>
          </div>
          <p className="text-sm text-slate-400 font-medium">
            {detail.route.departure_city} ({detail.departure_time}) →{" "}
            {detail.route.arrival_city} ({detail.arrival_time}) · {detail.departure_date}
          </p>
        </div>

        {/* Passenger count selector */}
        <div className="flex items-center gap-3">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-400">Seats to book:</label>
          <select
            value={passengerCount}
            onChange={(e) => setPassengerCount(Number(e.target.value))}
            className="rounded-lg border border-white/10 bg-[#0f172a]/60 backdrop-blur-md px-3.5 py-2 text-sm font-semibold text-slate-200 outline-none transition focus:border-white/20"
          >
            {Array.from({ length: MAX_PASSENGERS }, (_, i) => i + 1).map((n) => (
              <option key={n} value={n} className="bg-[#0f172a]">
                {n} Seat{n > 1 ? "s" : ""}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Grid of Seats inside Glass Card */}
      <div className="glass-panel rounded-xl p-6 sm:p-8 border-white/5">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-6">Select your seat(s)</h3>
        <SeatMap
          seats={detail.seats}
          selectedSeatIds={selectedIds}
          maxSelectable={passengerCount}
          onToggle={(seat) =>
            toggleSeat({ id: seat.id, seat_number: seat.seat_number, price: seat.price })
          }
        />
      </div>

      {/* Footer bar */}
      <div className="glass-panel flex items-center justify-between rounded-xl p-5 border-white/5">
        <div>
          <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">
            Selected {selectedSeats.length} of {passengerCount} seat{passengerCount > 1 ? "s" : ""}
          </p>
          <p className="text-2xl font-extrabold text-blue-400">
            Rs. {totalPrice.toLocaleString()}
          </p>
        </div>
        <Button
          onClick={handleContinue}
          disabled={selectedSeats.length !== passengerCount}
        >
          Continue
        </Button>
      </div>
    </div>
  );
}
