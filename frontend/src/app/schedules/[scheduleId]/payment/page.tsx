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
        // Real gateways (JazzCash/EasyPaisa once configured) redirect the
        // user to a hosted checkout page; the mock gateway never takes
        // this branch since it completes synchronously (see backend
        // app/payment/gateways/mock_gateway.py).
        window.location.href = paymentResult.redirect_url;
        return;
      }

      // Mock gateway path: payment is already COMPLETED by the time this
      // response comes back (see backend app/payment/service.py
      // initiate_payment, which calls confirm_payment synchronously for
      // non-redirect gateways).
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
      <div className="mx-auto max-w-md">
        <Alert variant="error">
          One of your selected seats was just booked by someone else. Please
          choose different seats.
        </Alert>
        <Button
          className="mt-4"
          onClick={() => router.push(`/schedules/${params.scheduleId}/seats`)}
        >
          Back to seat selection
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mb-6 text-2xl font-bold text-slate-900">Review & pay</h1>

      {errorMessage && <Alert variant="error">{errorMessage}</Alert>}

      <div className="mb-6 rounded-lg border border-slate-200 bg-white p-4">
        <p className="mb-2 text-sm font-medium text-slate-500">
          {selectedSeats.length} seat(s)
        </p>
        {selectedSeats.map((seat, i) => (
          <div key={seat.id} className="flex justify-between py-1 text-sm">
            <span>
              {passengers[i]?.first_name} {passengers[i]?.last_name} — Seat{" "}
              {seat.seat_number}
            </span>
            <span>Rs. {seat.price.toLocaleString()}</span>
          </div>
        ))}
        <div className="mt-3 flex justify-between border-t border-slate-200 pt-3 font-bold">
          <span>Total</span>
          <span>Rs. {totalPrice.toLocaleString()}</span>
        </div>
      </div>

      <Button
        onClick={handlePay}
        isLoading={stage === "creating_booking" || stage === "paying"}
        className="w-full"
      >
        {stage === "creating_booking"
          ? "Reserving seats…"
          : stage === "paying"
            ? "Processing payment…"
            : `Pay Rs. ${totalPrice.toLocaleString()}`}
      </Button>

      <p className="mt-3 text-center text-xs text-slate-400">
        Payments are processed via a mock gateway in this environment. No
        real charges will be made.
      </p>
    </div>
  );
}
