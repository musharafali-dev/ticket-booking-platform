"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useBookingFlowStore } from "@/store/booking-flow-store";
import { useAuthStore } from "@/store/auth-store";
import { TextField } from "@/components/text-field";
import { Button } from "@/components/button";
import { Alert } from "@/components/alert";

const formSchema = z.object({
  passengers: z.array(
    z.object({
      first_name: z.string().min(1, "Required"),
      last_name: z.string().min(1, "Required"),
    })
  ),
  contact_email: z.string().email("Enter a valid email address"),
  contact_phone: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

function BookingSteps({ currentStep }: { currentStep: 1 | 2 | 3 }) {
  return (
    <div className="flex items-center justify-center gap-3 mb-6 text-[10px] sm:text-xs font-bold uppercase tracking-wider">
      <span className={currentStep === 1 ? "text-blue-400" : "text-slate-500"}>
        1. Select Seats
      </span>
      <span className="text-slate-600">➔</span>
      <span className={currentStep === 2 ? "text-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.2)]" : "text-slate-500"}>
        2. Passengers Info
      </span>
      <span className="text-slate-600">➔</span>
      <span className={currentStep === 3 ? "text-blue-400" : "text-slate-500"}>
        3. Payment Checkout
      </span>
    </div>
  );
}

export default function PassengerDetailsPage() {
  const params = useParams<{ scheduleId: string }>();
  const router = useRouter();
  const selectedSeats = useBookingFlowStore((s) => s.selectedSeats);
  const setPassengers = useBookingFlowStore((s) => s.setPassengers);
  const setContactInfo = useBookingFlowStore((s) => s.setContactInfo);
  const user = useAuthStore((s) => s.user);

  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      passengers: selectedSeats.map(() => ({ first_name: "", last_name: "" })),
      contact_email: user?.email ?? "",
      contact_phone: user?.phone_number ?? "",
    },
  });

  const { fields } = useFieldArray({ control, name: "passengers" });

  useEffect(() => {
    if (selectedSeats.length === 0) {
      router.replace(`/schedules/${params.scheduleId}/seats`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSeats.length]);

  if (selectedSeats.length === 0) {
    return null;
  }

  const onSubmit = (values: FormValues) => {
    const passengers = values.passengers.map((p, i) => ({
      seat_id: selectedSeats[i]!.id,
      first_name: p.first_name,
      last_name: p.last_name,
    }));
    setPassengers(passengers);
    setContactInfo(values.contact_email, values.contact_phone ?? "");
    router.push(`/schedules/${params.scheduleId}/payment`);
  };

  return (
    <div className="mx-auto max-w-lg flex flex-col gap-6">
      {/* Steps Indicator */}
      <BookingSteps currentStep={2} />

      <div>
        <h1 className="mb-2 text-2xl font-extrabold text-white">Passenger Details</h1>
        <p className="text-sm text-slate-400">Provide names as they appear on official identity documents.</p>
      </div>

      {!user && (
        <Alert variant="info">
          You&apos;ll need to log in before completing this booking. You can fill in
          details now and we&apos;ll ask you to log in at checkout.
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">
        {/* Passenger Fields */}
        <div className="flex flex-col gap-4">
          {fields.map((field, index) => (
            <div key={field.id} className="glass-panel rounded-xl p-5 border-white/5 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b from-blue-500 to-indigo-500" />
              <p className="mb-4 text-xs font-bold uppercase tracking-wider text-blue-400">
                Seat {selectedSeats[index]?.seat_number} — Passenger #{index + 1}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <TextField
                  label="First name"
                  {...register(`passengers.${index}.first_name`)}
                  error={errors.passengers?.[index]?.first_name?.message}
                />
                <TextField
                  label="Last name"
                  {...register(`passengers.${index}.last_name`)}
                  error={errors.passengers?.[index]?.last_name?.message}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Contact Info Card */}
        <div className="glass-panel rounded-xl p-5 border-white/5">
          <p className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-400">Booking Contact</p>
          <div className="flex flex-col gap-4">
            <TextField
              label="Contact email"
              type="email"
              {...register("contact_email")}
              error={errors.contact_email?.message}
            />
            <TextField
              label="Contact phone (optional)"
              placeholder="+92-300-1234567"
              {...register("contact_phone")}
              error={errors.contact_phone?.message}
            />
          </div>
        </div>

        <Button type="submit" className="py-3">
          Continue to Payment
        </Button>
      </form>
    </div>
  );
}
