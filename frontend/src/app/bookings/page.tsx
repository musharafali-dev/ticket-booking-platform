"use client";

import Link from "next/link";
import useSWR from "swr";
import type { Booking, BookingStatus } from "@/types/api";
import { Alert } from "@/components/alert";
import { useAuthStore } from "@/store/auth-store";
import clsx from "clsx";

const STATUS_STYLES: Record<BookingStatus, string> = {
  PENDING: "bg-amber-500/10 border border-amber-500/25 text-amber-300 shadow-[0_0_12px_rgba(245,158,11,0.05)]",
  CONFIRMED: "bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.05)]",
  CANCELLED: "bg-slate-500/10 border border-slate-500/25 text-slate-400",
  EXPIRED: "bg-red-500/10 border border-red-500/25 text-red-300 shadow-[0_0_12px_rgba(239,68,68,0.05)]",
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
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20" role="status">
        <svg className="h-8 w-8 animate-spin text-orange-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p className="text-slate-400 font-medium">Loading your bookings…</p>
      </div>
    );
  }

  if (error) {
    return <Alert variant="error">Could not load your bookings.</Alert>;
  }

  if (!bookings || bookings.length === 0) {
    return (
      <div className="text-center py-12 glass-panel rounded-xl p-8 border-white/5 max-w-md mx-auto">
        <span className="text-4xl mb-4 block">🎫</span>
        <p className="mb-6 text-slate-400 font-medium">You haven&apos;t made any ticket bookings yet.</p>
        <Link href="/" className="inline-flex rounded-lg bg-orange-600 px-4 py-2 text-sm font-semibold text-white hover:bg-orange-500 transition duration-300">
          Book a Trip Now
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5 max-w-xl mx-auto">
      <div>
        <h1 className="text-2xl font-extrabold text-white mb-1">My Bookings</h1>
        <p className="text-sm text-slate-400">View and manage your upcoming and past bookings.</p>
      </div>

      <div className="flex flex-col gap-3">
        {bookings.map((booking) => (
          <Link
            key={booking.id}
            href={`/bookings/${booking.id}/confirmation`}
            className="glass-card flex items-center justify-between rounded-xl p-5 border-white/5 transition hover:border-orange-500/40"
          >
            <div className="flex flex-col gap-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Booking Code</span>
              <p className="font-mono text-sm font-bold text-white tracking-wider">
                {booking.booking_code}
              </p>
              <p className="text-xs text-slate-400 mt-1 font-medium">
                {booking.number_of_passengers} Passenger{booking.number_of_passengers > 1 ? "s" : ""} · Rs.{" "}
                {booking.total_amount.toLocaleString()}
              </p>
            </div>
            <span
              className={clsx(
                "rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider",
                STATUS_STYLES[booking.status]
              )}
            >
              {booking.status}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
