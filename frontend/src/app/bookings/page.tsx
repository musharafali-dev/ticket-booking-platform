"use client";

import Link from "next/link";
import useSWR from "swr";
import type { Booking, BookingStatus } from "@/types/api";
import { Alert } from "@/components/alert";
import { useAuthStore } from "@/store/auth-store";
import clsx from "clsx";

const STATUS_STYLES: Record<BookingStatus, string> = {
  PENDING: "bg-amber-50 text-amber-700",
  CONFIRMED: "bg-green-50 text-green-700",
  CANCELLED: "bg-slate-100 text-slate-500",
  EXPIRED: "bg-red-50 text-red-600",
};

export default function BookingsPage() {
  const user = useAuthStore((s) => s.user);
  const { data: bookings, error, isLoading } = useSWR<Booking[]>(
    user ? "/bookings" : null
  );

  if (!user) {
    return <Alert variant="info">Please log in to see your bookings.</Alert>;
  }

  if (isLoading) {
    return <p className="text-center text-slate-500" role="status">Loading your bookings…</p>;
  }

  if (error) {
    return <Alert variant="error">Could not load your bookings.</Alert>;
  }

  if (!bookings || bookings.length === 0) {
    return (
      <div className="text-center text-slate-500">
        <p className="mb-4">You haven&apos;t made any bookings yet.</p>
        <Link href="/" className="text-brand-600 underline">
          Search for a trip
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold text-slate-900">My bookings</h1>

      {bookings.map((booking) => (
        <Link
          key={booking.id}
          href={`/bookings/${booking.id}/confirmation`}
          className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4 transition hover:border-brand-500"
        >
          <div>
            <p className="font-mono text-sm font-medium text-slate-900">
              {booking.booking_code}
            </p>
            <p className="text-sm text-slate-500">
              {booking.number_of_passengers} passenger(s) · Rs.{" "}
              {booking.total_amount.toLocaleString()}
            </p>
          </div>
          <span
            className={clsx(
              "rounded-full px-2.5 py-0.5 text-xs font-medium",
              STATUS_STYLES[booking.status]
            )}
          >
            {booking.status}
          </span>
        </Link>
      ))}
    </div>
  );
}
