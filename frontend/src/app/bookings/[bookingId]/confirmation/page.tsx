"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import useSWR, { useSWRConfig } from "swr";
import { useState } from "react";
import type { Booking } from "@/types/api";
import { Alert } from "@/components/alert";
import { Button } from "@/components/button";
import { apiClient, ApiError } from "@/lib/api-client";

export default function ConfirmationPage() {
  const params = useParams<{ bookingId: string }>();
  const bookingId = Number(params.bookingId);
  const router = useRouter();
  const { mutate } = useSWRConfig();

  const { data: booking, error, isLoading } = useSWR<Booking>(
    Number.isFinite(bookingId) ? `/bookings/${bookingId}` : null
  );

  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("Change of plans");
  const [customReason, setCustomReason] = useState("");
  const [isCancelling, setIsCancelling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20" role="status">
        <svg className="h-8 w-8 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p className="text-slate-400 font-medium">Loading your booking receipt...</p>
      </div>
    );
  }

  if (error || !booking) {
    return <Alert variant="error">Could not load this booking.</Alert>;
  }

  const isConfirmed = booking.status === "CONFIRMED";
  const isCancelled = booking.status === "CANCELLED";
  const isPending = booking.status === "PENDING";
  const isExpired = booking.status === "EXPIRED";

  const handleCancelBooking = async () => {
    setIsCancelling(true);
    setCancelError(null);
    try {
      const reason = cancelReason === "Other" ? customReason : cancelReason;
      await apiClient.post(`/bookings/${booking.id}/cancel`, { reason });
      await mutate(`/bookings/${bookingId}`);
      setIsCancelModalOpen(false);
    } catch (err) {
      setCancelError(err instanceof ApiError ? err.detail : "Could not cancel booking. Try again.");
    } finally {
      setIsCancelling(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="mx-auto max-w-lg flex flex-col gap-6">
      {/* Print stylesheet injected directly */}
      <style dangerouslySetInnerHTML={{ __html: `
        @media print {
          body {
            background: white !important;
            color: black !important;
          }
          header, nav, button, a, .no-print {
            display: none !important;
          }
          .print-ticket {
            background: white !important;
            color: black !important;
            border: 2px dashed #475569 !important;
            box-shadow: none !important;
            margin: 0 !important;
            padding: 32px !important;
            width: 100% !important;
            position: absolute;
            top: 0;
            left: 0;
          }
          .print-ticket * {
            color: black !important;
          }
          .ticket-tear-left, .ticket-tear-right {
            display: none !important;
          }
        }
      ` }} />

      {/* Success/Pending Header Icon */}
      <div className="text-center no-print mt-4">
        <div
          className={`mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full text-3xl shadow-lg transition duration-500 ${
            isConfirmed ? "bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.2)]" :
            isPending ? "bg-amber-500/10 border border-amber-500/25 text-amber-400 shadow-[0_0_20px_rgba(245,158,11,0.2)] animate-pulse" :
            isCancelled ? "bg-slate-500/10 border border-slate-500/25 text-slate-400" :
            "bg-red-500/10 border border-red-500/25 text-red-400"
          }`}
        >
          {isConfirmed ? "✅" : isPending ? "⏳" : isCancelled ? "🚫" : "❌"}
        </div>

        <h1 className="mb-1 text-3xl font-extrabold text-white">
          {isConfirmed ? "Booking Confirmed!" :
           isPending ? "Booking Pending Payment" :
           isCancelled ? "Booking Cancelled" : "Booking Expired"}
        </h1>
        <p className="text-slate-400 text-sm">
          Booking reference: <span className="font-mono font-bold text-white tracking-widest">{booking.booking_code}</span>
        </p>
      </div>

      {/* Digital Ticket Layout */}
      <div className="print-ticket glass-panel rounded-2xl relative overflow-hidden p-6 border-white/10 shadow-2xl flex flex-col">
        {/* Ticket Tears (Boarding pass look) */}
        <div className="ticket-tear-left" />
        <div className="ticket-tear-right" />

        {/* Ticket Header */}
        <div className="flex justify-between items-start border-b border-white/5 pb-4 mb-4">
          <div>
            <span className="text-[9px] font-bold uppercase tracking-widest text-slate-500 block mb-0.5">Ticket Type</span>
            <span className="text-xs font-bold text-white uppercase tracking-wider bg-white/5 border border-white/10 px-2 py-0.5 rounded">
              Digital Boarding Pass
            </span>
          </div>
          <div className="text-right">
            <span className="text-[9px] font-bold uppercase tracking-widest text-slate-500 block mb-0.5">Reference</span>
            <span className="font-mono font-bold text-blue-400 tracking-wider text-sm">{booking.booking_code}</span>
          </div>
        </div>

        {/* Ticket Details */}
        <div className="grid grid-cols-2 gap-4 pb-4">
          <div>
            <span className="text-[9px] font-bold uppercase tracking-widest text-slate-500 block mb-0.5">Passengers</span>
            <span className="text-sm font-bold text-slate-200">{booking.number_of_passengers} Traveller(s)</span>
          </div>
          <div className="text-right">
            <span className="text-[9px] font-bold uppercase tracking-widest text-slate-500 block mb-0.5">Status</span>
            <span className={`text-xs font-bold uppercase ${
              isConfirmed ? "text-emerald-400" :
              isPending ? "text-amber-400" :
              isCancelled ? "text-slate-400" : "text-red-400"
            }`}>
              {booking.status}
            </span>
          </div>
        </div>

        {/* Dashed Separator */}
        <div className="border-t-2 border-dashed border-white/10 my-2 relative" />

        {/* Ticket Body / Passengers & Seats */}
        <div className="py-3 flex flex-col gap-2">
          <span className="text-[9px] font-bold uppercase tracking-widest text-slate-500 block mb-1">Manifest</span>
          {booking.passengers.map((p) => (
            <div key={p.id} className="flex justify-between items-center text-sm py-0.5">
              <span className="font-medium text-slate-300">
                {p.first_name} {p.last_name}
              </span>
              <span className="font-mono text-xs font-semibold text-slate-100 bg-white/5 border border-white/5 rounded px-2 py-0.5">
                Seat {p.seat_number}
              </span>
            </div>
          ))}
        </div>

        {/* Ticket Divider */}
        <div className="border-t-2 border-dashed border-white/10 my-2 relative" />

        {/* Ticket Bottom / Fare & Barcode */}
        <div className="pt-4 flex flex-col gap-5">
          <div className="flex justify-between items-end">
            <div>
              <span className="text-[9px] font-bold uppercase tracking-widest text-slate-500 block mb-0.5">Payment Method</span>
              <span className="text-xs font-semibold text-slate-300">Mock Sandbox Checkout</span>
            </div>
            <div className="text-right">
              <span className="text-[9px] font-bold uppercase tracking-widest text-slate-500 block mb-0.5">Total Paid</span>
              <span className="text-xl font-extrabold text-blue-400">
                Rs. {booking.total_amount.toLocaleString()}
              </span>
            </div>
          </div>

          {/* Barcode Visualizer */}
          <div className="flex flex-col items-center mt-2">
            <div className="flex justify-center items-center gap-[2px] h-12 w-full max-w-[280px] bg-white/5 border border-white/5 rounded p-2 opacity-65">
              {Array.from({ length: 35 }).map((_, i) => (
                <div
                  key={i}
                  className="h-full bg-slate-300"
                  style={{ width: `${(i % 5 === 0 ? 3 : i % 3 === 0 ? 1 : 2)}px` }}
                />
              ))}
            </div>
            <span className="text-[9px] font-mono tracking-widest text-slate-500 mt-1.5">
              {booking.booking_code}-{booking.id}
            </span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="no-print flex flex-col sm:flex-row justify-center gap-3 mt-4 pb-6">
        <Link href="/bookings">
          <Button variant="secondary" className="w-full sm:w-auto">My Bookings</Button>
        </Link>
        <Button onClick={handlePrint} className="w-full sm:w-auto">
          🖨️ Print Ticket
        </Button>
        {(isConfirmed || isPending) && (
          <Button
            variant="danger"
            onClick={() => setIsCancelModalOpen(true)}
            className="w-full sm:w-auto"
          >
            🚫 Cancel Booking
          </Button>
        )}
      </div>

      {/* Booking Cancellation Glass Modal */}
      {isCancelModalOpen && (
        <div className="fixed inset-0 z-50 bg-[#070913]/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="glass-panel rounded-2xl max-w-md w-full p-6 border-white/10 shadow-2xl relative flex flex-col gap-5 animate-in zoom-in-95 duration-200">
            <div>
              <h3 className="text-xl font-extrabold text-white mb-1">Cancel Booking</h3>
              <p className="text-xs text-slate-400">This action will release your reserved seat(s) immediately.</p>
            </div>

            {cancelError && <Alert variant="error">{cancelError}</Alert>}

            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-400">Reason for Cancellation</label>
                <select
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  className="rounded-lg border border-white/10 bg-[#0f172a]/60 backdrop-blur-md px-3.5 py-2.5 text-sm font-semibold text-slate-200 outline-none transition focus:border-white/20"
                >
                  <option className="bg-[#0f172a]" value="Change of plans">Change of plans</option>
                  <option className="bg-[#0f172a]" value="Personal emergency">Personal emergency</option>
                  <option className="bg-[#0f172a]" value="Booking mistake">Booking mistake</option>
                  <option className="bg-[#0f172a]" value="Other">Other (Please specify)</option>
                </select>
              </div>

              {cancelReason === "Other" && (
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-400">Details</label>
                  <textarea
                    required
                    value={customReason}
                    onChange={(e) => setCustomReason(e.target.value)}
                    placeholder="Provide details about your cancellation..."
                    rows={3}
                    className="glass-input rounded-lg px-3.5 py-2.5 text-sm outline-none w-full resize-none focus:border-blue-500 focus:shadow-[0_0_15px_rgba(59,130,246,0.25)]"
                  />
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-2">
              <Button
                variant="secondary"
                onClick={() => {
                  setIsCancelModalOpen(false);
                  setCancelError(null);
                }}
                disabled={isCancelling}
              >
                No, Keep Booking
              </Button>
              <Button
                variant="danger"
                onClick={handleCancelBooking}
                isLoading={isCancelling}
              >
                Yes, Cancel Booking
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
