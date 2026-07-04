"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import useSWR from "swr";
import type { Booking } from "@/types/api";
import { Alert } from "@/components/alert";
import { Button } from "@/components/button";

export default function ConfirmationPage() {
  const params = useParams<{ bookingId: string }>();
  const bookingId = Number(params.bookingId);

  const { data: booking, error, isLoading } = useSWR<Booking>(
    Number.isFinite(bookingId) ? `/bookings/${bookingId}` : null
  );

  if (isLoading) {
    return <p className="text-center text-slate-500" role="status">Loading your booking…</p>;
  }

  if (error || !booking) {
    return <Alert variant="error">Could not load this booking.</Alert>;
  }

  const isConfirmed = booking.status === "CONFIRMED";

  return (
    <div className="mx-auto max-w-lg text-center">
      <div
        className={`mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full text-3xl ${
          isConfirmed ? "bg-green-100" : "bg-amber-100"
        }`}
      >
        {isConfirmed ? "✅" : "⏳"}
      </div>

      <h1 className="mb-2 text-2xl font-bold text-slate-900">
        {isConfirmed ? "Booking confirmed!" : `Booking ${booking.status.toLowerCase()}`}
      </h1>
      <p className="mb-6 text-slate-600">
        Booking reference: <span className="font-mono font-medium">{booking.booking_code}</span>
      </p>

      <div className="mb-6 rounded-lg border border-slate-200 bg-white p-4 text-left">
        <p className="mb-2 text-sm font-medium text-slate-500">
          {booking.number_of_passengers} passenger(s)
        </p>
        {booking.passengers.map((p) => (
          <div key={p.id} className="flex justify-between py-1 text-sm">
            <span>
              {p.first_name} {p.last_name}
            </span>
            <span className="text-slate-500">Seat {p.seat_number}</span>
          </div>
        ))}
        <div className="mt-3 flex justify-between border-t border-slate-200 pt-3 font-bold">
          <span>Total paid</span>
          <span>Rs. {booking.total_amount.toLocaleString()}</span>
        </div>
      </div>

      <div className="flex justify-center gap-3">
        <Link href="/bookings">
          <Button variant="secondary">View my bookings</Button>
        </Link>
        <Link href="/">
          <Button>Book another trip</Button>
        </Link>
      </div>
    </div>
  );
}
