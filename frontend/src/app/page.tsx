"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useScheduleSearch } from "@/hooks/use-schedule-search";
import { useBookingFlowStore } from "@/store/booking-flow-store";
import { TransportBadge } from "@/components/transport-badge";
import { Button } from "@/components/button";
import { Alert } from "@/components/alert";
import type { TransportType } from "@/types/api";

function todayIsoDate(): string {
  return new Date().toISOString().split("T")[0] ?? "";
}

export default function SearchPage() {
  const router = useRouter();
  const setSchedule = useBookingFlowStore((s) => s.setSchedule);

  const [departureCity, setDepartureCity] = useState("Karachi");
  const [arrivalCity, setArrivalCity] = useState("Lahore");
  const [departureDate, setDepartureDate] = useState(todayIsoDate());
  const [transportType, setTransportType] = useState<TransportType | "">("");
  const [submittedParams, setSubmittedParams] = useState<{
    departureCity: string;
    arrivalCity: string;
    departureDate: string;
    transportType?: string;
  } | null>(null);

  const { data: results, error, isLoading } = useScheduleSearch(submittedParams);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedParams({
      departureCity,
      arrivalCity,
      departureDate,
      transportType: transportType || undefined,
    });
  };

  const handleSelectSchedule = (schedule: NonNullable<typeof results>[number]) => {
    setSchedule(schedule);
    router.push(`/schedules/${schedule.id}/seats`);
  };

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="mb-1 text-2xl font-bold text-slate-900">
          Book bus, train & flight tickets across Pakistan
        </h1>
        <p className="text-slate-600">Search live availability and book in minutes.</p>
      </div>

      <form
        onSubmit={handleSearch}
        className="grid grid-cols-1 gap-4 rounded-lg border border-slate-200 bg-white p-6 sm:grid-cols-2 lg:grid-cols-5"
      >
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-slate-700">From</label>
          <input
            required
            value={departureCity}
            onChange={(e) => setDepartureCity(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Karachi"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-slate-700">To</label>
          <input
            required
            value={arrivalCity}
            onChange={(e) => setArrivalCity(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Lahore"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-slate-700">Date</label>
          <input
            required
            type="date"
            min={todayIsoDate()}
            value={departureDate}
            onChange={(e) => setDepartureDate(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-slate-700">Type</label>
          <select
            value={transportType}
            onChange={(e) => setTransportType(e.target.value as TransportType | "")}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">Any</option>
            <option value="BUS">Bus</option>
            <option value="TRAIN">Train</option>
            <option value="AIRPLANE">Flight</option>
          </select>
        </div>

        <div className="flex items-end">
          <Button type="submit" className="w-full">
            Search
          </Button>
        </div>
      </form>

      {isLoading && (
        <p className="text-center text-slate-500" role="status">
          Searching for schedules…
        </p>
      )}

      {error && <Alert variant="error">Could not load results. Please try again.</Alert>}

      {submittedParams && !isLoading && !error && results?.length === 0 && (
        <Alert variant="info">
          No schedules found for {submittedParams.departureCity} →{" "}
          {submittedParams.arrivalCity} on {submittedParams.departureDate}. Try a
          different date or route.
        </Alert>
      )}

      {results && results.length > 0 && (
        <div className="flex flex-col gap-3">
          {results.map((schedule) => (
            <button
              key={schedule.id}
              onClick={() => handleSelectSchedule(schedule)}
              className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4 text-left transition hover:border-brand-500 hover:shadow-sm"
            >
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <TransportBadge type={schedule.operator.operator_type} />
                  <span className="font-medium text-slate-900">
                    {schedule.operator.operator_name}
                  </span>
                </div>
                <p className="text-sm text-slate-600">
                  {schedule.route.departure_city} ({schedule.departure_time}) →{" "}
                  {schedule.route.arrival_city} ({schedule.arrival_time})
                </p>
                <p className="text-xs text-slate-400">
                  {schedule.available_seats} of {schedule.total_seats} seats available
                </p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-slate-900">
                  Rs. {schedule.base_fare.toLocaleString()}
                </p>
                <p className="text-xs text-slate-400">per seat</p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
