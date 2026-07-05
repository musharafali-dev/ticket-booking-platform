"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useBookingFlowStore } from "@/store/booking-flow-store";
import { useAuthStore } from "@/store/auth-store";
import { apiClient, ApiError } from "@/lib/api-client";
import type { Booking, BookingCreateRequest, PaymentInitiateResponse } from "@/types/api";
import { Button } from "@/components/button";
import { Alert } from "@/components/alert";

type Stage = "review" | "creating_booking" | "paying" | "seat_conflict" | "error";

function BookingSteps({ currentStep }: { currentStep: 1 | 2 | 3 }) {
  return (
    <div className="flex items-center justify-center gap-3 mb-6 text-[10px] sm:text-xs font-bold uppercase tracking-wider">
      <span className={currentStep === 1 ? "text-blue-400" : "text-slate-500"}>
        1. Select Seats
      </span>
      <span className="text-slate-600">➔</span>
      <span className={currentStep === 2 ? "text-blue-400" : "text-slate-500"}>
        2. Passengers Info
      </span>
      <span className="text-slate-600">➔</span>
      <span className={currentStep === 3 ? "text-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.2)]" : "text-slate-500"}>
        3. Payment Checkout
      </span>
    </div>
  );
}

export default function PaymentPage() {
  const params = useParams<{ scheduleId: string }>();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const { selectedSeats, passengers, contactEmail, contactPhone, reset } =
    useBookingFlowStore();

  const [stage, setStage] = useState<Stage>("review");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (selectedSeats.length === 0 || passengers.length === 0) {
      router.replace(`/schedules/${params.scheduleId}/seats`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalPrice = selectedSeats.reduce((sum, s) => sum + s.price, 0);

  const handlePay = async () => {
    if (!user) {
      router.push(`/login?next=/schedules/${params.scheduleId}/payment`);
      return;
    }

    setErrorMessage(null);
    setStage("creating_booking");

    try {
      const bookingRequest: BookingCreateRequest = {
        schedule_id: Number(params.scheduleId),
        passengers,
        contact_email: contactEmail,
        contact_phone: contactPhone || undefined,
      };

      const createdBooking = await apiClient.post<Booking>("/bookings", bookingRequest);
      setStage("paying");

      const paymentResult = await apiClient.post<PaymentInitiateResponse>(
        "/payments/initiate",
        { booking_id: createdBooking.id }
      );

      if (paymentResult.requires_redirect && paymentResult.redirect_url) {
        window.location.href = paymentResult.redirect_url;
        return;
      }

      reset();
      router.push(`/bookings/${createdBooking.id}/confirmation`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setStage("seat_conflict");
      } else {
        setErrorMessage(err instanceof ApiError ? err.detail : "Something went wrong.");
        setStage("error");
      }
    }
  };

  if (selectedSeats.length === 0) {
    return null;
  }

  if (stage === "seat_conflict") {
    return (
      <div className="mx-auto max-w-md flex flex-col gap-6">
        <BookingSteps currentStep={3} />
        <Alert variant="error">
          One of your selected seats was just booked by someone else. Please
          choose different seats.
        </Alert>
        <Button
          onClick={() => router.push(`/schedules/${params.scheduleId}/seats`)}
        >
          Back to seat selection
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md flex flex-col gap-6">
      {/* Steps Indicator */}
      <BookingSteps currentStep={3} />

      <div>
        <h1 className="mb-2 text-2xl font-extrabold text-white">Review & Pay</h1>
        <p className="text-sm text-slate-400">Please review your trip details and complete payment.</p>
      </div>

      {errorMessage && <Alert variant="error">{errorMessage}</Alert>}

      {/* Booking Summary Glass Card */}
      <div className="glass-panel rounded-xl p-5 border-white/5 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b from-blue-500 to-indigo-500" />
        <p className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-400">
          Booking Summary
        </p>

        <div className="flex flex-col gap-3">
          {selectedSeats.map((seat, i) => (
            <div key={seat.id} className="flex justify-between items-center text-sm">
              <div className="flex flex-col">
                <span className="font-semibold text-slate-200">
                  {passengers[i]?.first_name} {passengers[i]?.last_name}
                </span>
                <span className="text-xs text-slate-400">Seat {seat.seat_number}</span>
              </div>
              <span className="font-bold text-slate-300">Rs. {seat.price.toLocaleString()}</span>
            </div>
          ))}

          <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-end">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Fare</span>
            <span className="text-2xl font-extrabold text-blue-400">
              Rs. {totalPrice.toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <Button
          onClick={handlePay}
          isLoading={stage === "creating_booking" || stage === "paying"}
          className="w-full py-3"
        >
          {stage === "creating_booking"
            ? "Reserving seats…"
            : stage === "paying"
              ? "Processing payment…"
              : `Pay Rs. ${totalPrice.toLocaleString()}`}
        </Button>

        <p className="text-center text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
          🔒 Secure Checkout · Demo Sandbox
        </p>
      </div>
    </div>
  );
}
