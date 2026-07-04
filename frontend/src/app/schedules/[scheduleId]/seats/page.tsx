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

  // If the user reduces passenger count below their current selection,
  // trim the excess rather than leaving an inconsistent state where
  // selectedSeats.length > passengerCount silently persists.
  useEffect(() => {
    if (selectedSeats.length > passengerCount) {
      const excess = selectedSeats.slice(passengerCount);
      excess.forEach((s) => toggleSeat(s));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [passengerCount]);

  if (isLoading) {
    return <p className="text-center text-slate-500" role="status">Loading seat map…</p>;
  }

  if (error || !detail) {
    return (
      <Alert variant="error">
        Could not load this schedule. It may no longer be available.{" "}
        <button onClick={() => router.push("/")} className="underline">
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
    <div className="flex flex-col gap-6">
      <div>
        <div className="mb-1 flex items-center gap-2">
          <TransportBadge type={detail.operator.operator_type} />
          <h1 className="text-xl font-bold text-slate-900">{detail.operator.operator_name}</h1>
        </div>
        <p className="text-slate-600">
          {detail.route.departure_city} ({detail.departure_time}) →{" "}
          {detail.route.arrival_city} ({detail.arrival_time}) · {detail.departure_date}
        </p>
      </div>

      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-slate-700">Passengers</label>
        <select
          value={passengerCount}
          onChange={(e) => setPassengerCount(Number(e.target.value))}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        >
          {Array.from({ length: MAX_PASSENGERS }, (_, i) => i + 1).map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <SeatMap
          seats={detail.seats}
          selectedSeatIds={selectedIds}
          maxSelectable={passengerCount}
          onToggle={(seat) =>
            toggleSeat({ id: seat.id, seat_number: seat.seat_number, price: seat.price })
          }
        />
      </div>

      <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <p className="text-sm text-slate-600">
            {selectedSeats.length} of {passengerCount} seat(s) selected
          </p>
          <p className="text-lg font-bold text-slate-900">
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
