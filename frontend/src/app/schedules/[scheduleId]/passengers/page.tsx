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
    <div className="mx-auto max-w-lg">
      <h1 className="mb-6 text-2xl font-bold text-slate-900">Passenger details</h1>

      {!user && (
        <Alert variant="info">
          You&apos;ll need to log in before completing this booking. You can fill in
          details now and we&apos;ll ask you to log in at checkout.
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="mt-4 flex flex-col gap-6">
        {fields.map((field, index) => (
          <div key={field.id} className="rounded-lg border border-slate-200 p-4">
            <p className="mb-3 text-sm font-medium text-slate-500">
              Seat {selectedSeats[index]?.seat_number}
            </p>
            <div className="grid grid-cols-2 gap-4">
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

        <div className="rounded-lg border border-slate-200 p-4">
          <p className="mb-3 text-sm font-medium text-slate-500">Booking contact</p>
          <div className="flex flex-col gap-4">
            <TextField
              label="Contact email"
              type="email"
              {...register("contact_email")}
              error={errors.contact_email?.message}
            />
            <TextField
              label="Contact phone (optional)"
              {...register("contact_phone")}
              error={errors.contact_phone?.message}
            />
          </div>
        </div>

        <Button type="submit">Continue to payment</Button>
      </form>
    </div>
  );
}
