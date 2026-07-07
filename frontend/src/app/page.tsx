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

function formatDuration(minutes: number | null): string {
  if (!minutes) return "N/A";
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
}

export default function SearchPage() {
  const router = useRouter();
  const setSchedule = useBookingFlowStore((s) => s.setSchedule);

  const [departureCity, setDepartureCity] = useState("Karachi");
  const [arrivalCity, setArrivalCity] = useState("Lahore");
  const [departureDate, setDepartureDate] = useState(todayIsoDate());
  const [transportType, setTransportType] = useState<TransportType | "">("");
  const [isSwapping, setIsSwapping] = useState(false);
  const [sortBy, setSortBy] = useState<"price-asc" | "price-desc" | "time-asc" | "time-desc" | "seats-desc">("price-asc");

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

  const handleSwapCities = () => {
    setIsSwapping(true);
    const temp = departureCity;
    setDepartureCity(arrivalCity);
    setArrivalCity(temp);
    setTimeout(() => setIsSwapping(false), 500);

    if (submittedParams) {
      setSubmittedParams({
        departureCity: arrivalCity,
        arrivalCity: temp,
        departureDate,
        transportType: transportType || undefined,
      });
    }
  };

  const processedResults = results
    ? [...results].sort((a, b) => {
        if (sortBy === "price-asc") return a.base_fare - b.base_fare;
        if (sortBy === "price-desc") return b.base_fare - a.base_fare;
        if (sortBy === "time-asc") return a.departure_time.localeCompare(b.departure_time);
        if (sortBy === "time-desc") return b.departure_time.localeCompare(a.departure_time);
        if (sortBy === "seats-desc") return b.available_seats - a.available_seats;
        return 0;
      })
    : [];

  return (
    <div className="flex flex-col gap-8 max-w-4xl mx-auto">
      {/* Hero Section */}
      <div className="text-center py-6">
        <h1 className="mb-3 text-4xl font-extrabold tracking-tight sm:text-5xl bg-gradient-to-r from-orange-400 via-amber-200 to-indigo-400 bg-clip-text text-transparent">
          Book Bus, Train & Flight Tickets
        </h1>
        <p className="text-slate-400 text-lg max-w-xl mx-auto font-medium">
          Search live schedules and book seats instantly across Pakistan.
        </p>
      </div>

      {/* Glassmorphic Form Card */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 shadow-2xl relative border-white/5">
        {/* Mode Selector Tabs */}
        <div className="flex justify-center sm:justify-start gap-2 mb-6 border-b border-white/5 pb-5 overflow-x-auto">
          {[
            {
              id: "",
              label: "All Modes",
              icon: (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
              ),
            },
            {
              id: "BUS",
              label: "Bus",
              icon: (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 18.75a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0ZM7.5 18.75a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0ZM2.25 15h19.5M3 18.75h18M4.5 5.25h15a2.25 2.25 0 0 1 2.25 2.25v7.5a2.25 2.25 0 0 1-2.25 2.25h-15A2.25 2.25 0 0 1 2.25 15v-7.5A2.25 2.25 0 0 1 4.5 5.25Zm0 4.5h15v-1.5h-15v1.5Zm0 3.75h15v-1.5h-15v1.5Z" />
                </svg>
              ),
            },
            {
              id: "TRAIN",
              label: "Train",
              icon: (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5.25 19.5h13.5M5.25 4.5h13.5m-10.5 3h7.5m-7.5 3h7.5m-7.5 3h7.5M5.25 4.5A2.25 2.25 0 0 0 3 6.75v10.5A2.25 2.25 0 0 0 5.25 19.5M18.75 4.5A2.25 2.25 0 0 1 21 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25M6 19.5l-1.5 3m13.5-3 1.5 3" />
                </svg>
              ),
            },
            {
              id: "AIRPLANE",
              label: "Flight",
              icon: (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L6 12Zm0 0h7.5" />
                </svg>
              ),
            },
          ].map((mode) => (
            <button
              key={mode.id}
              type="button"
              onClick={() => {
                setTransportType(mode.id as TransportType | "");
                if (submittedParams) {
                  setSubmittedParams((prev) =>
                    prev
                      ? {
                          ...prev,
                          transportType: mode.id || undefined,
                        }
                      : null
                  );
                }
              }}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-all duration-300 ${
                transportType === mode.id
                  ? "bg-orange-500/10 border border-orange-500/30 text-orange-400 shadow-[0_0_15px_rgba(249,115,22,0.15)]"
                  : "border border-transparent text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              {mode.icon}
              <span>{mode.label}</span>
            </button>
          ))}
        </div>

        <form onSubmit={handleSearch} className="flex flex-col gap-6">
          <div className="grid grid-cols-1 gap-5 md:grid-cols-7 items-end">
            {/* Departure City */}
            <div className="flex flex-col gap-1.5 md:col-span-3">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-400">From</label>
              <input
                required
                value={departureCity}
                onChange={(e) => setDepartureCity(e.target.value)}
                className="glass-input rounded-lg px-4 py-3 text-sm focus:ring-0 focus:outline-none"
                placeholder="e.g. Karachi"
              />
            </div>

            {/* City Swap Button */}
            <div className="flex justify-center items-center py-2 md:col-span-1 md:py-0 md:pb-2">
              <button
                type="button"
                onClick={handleSwapCities}
                title="Swap cities"
                className={`flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-300 transition-all duration-500 hover:bg-white/10 hover:border-orange-500/50 hover:text-orange-400 ${
                  isSwapping ? "rotate-180 scale-95" : ""
                }`}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="2.5"
                  stroke="currentColor"
                  className="h-5 w-5"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5"
                  />
                </svg>
              </button>
            </div>

            {/* Arrival City */}
            <div className="flex flex-col gap-1.5 md:col-span-3">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-400">To</label>
              <input
                required
                value={arrivalCity}
                onChange={(e) => setArrivalCity(e.target.value)}
                className="glass-input rounded-lg px-4 py-3 text-sm focus:ring-0 focus:outline-none"
                placeholder="e.g. Lahore"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 md:grid-cols-3 items-end">
            {/* Departure Date */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-400">Departure Date</label>
              <input
                required
                type="date"
                min={todayIsoDate()}
                value={departureDate}
                onChange={(e) => setDepartureDate(e.target.value)}
                className="glass-input rounded-lg px-4 py-3 text-sm focus:ring-0 focus:outline-none [color-scheme:dark]"
              />
            </div>

            <div className="hidden md:block"></div>

            {/* Submit Button */}
            <div className="flex items-end">
              <Button type="submit" className="w-full py-3">
                Search Schedules
              </Button>
            </div>
          </div>
        </form>

        {/* Popular Routes Section */}
        <div className="mt-6 pt-5 border-t border-white/5">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Popular Routes</p>
          <div className="flex flex-wrap gap-2">
            {[
              { from: "Karachi", to: "Lahore" },
              { from: "Lahore", to: "Islamabad" },
              { from: "Karachi", to: "Islamabad" },
              { from: "Peshawar", to: "Islamabad" },
              { from: "Multan", to: "Lahore" },
            ].map((route, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setDepartureCity(route.from);
                  setArrivalCity(route.to);
                  // Trigger search with selected route parameters
                  setSubmittedParams({
                    departureCity: route.from,
                    arrivalCity: route.to,
                    departureDate,
                    transportType: transportType || undefined,
                  });
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border border-white/10 bg-white/5 text-slate-300 hover:bg-orange-500/10 hover:border-orange-500/30 hover:text-orange-400 transition-all duration-300"
              >
                <span>{route.from}</span>
                <svg className="w-3 h-3 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
                <span>{route.to}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="flex flex-col items-center justify-center gap-3 py-10" role="status">
          <svg className="h-8 w-8 animate-spin text-orange-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-slate-400 font-medium animate-pulse">Searching active routes...</p>
        </div>
      )}

      {error && <Alert variant="error">Could not fetch schedules. Please check your connection and try again.</Alert>}

      {submittedParams && !isLoading && !error && processedResults.length === 0 && (
        <Alert variant="info">
          No schedules found for <span className="font-semibold text-white">{submittedParams.departureCity}</span> →{" "}
          <span className="font-semibold text-white">{submittedParams.arrivalCity}</span> on {submittedParams.departureDate}. Try a
          different date, city, or filter.
        </Alert>
      )}

      {/* Results Section */}
      {submittedParams && processedResults.length > 0 && (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 px-1">
            <p className="text-sm font-semibold text-slate-400">
              Found <span className="text-white">{processedResults.length}</span> schedules
            </p>

            {/* Sorting Dropdown */}
            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Sort By:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="rounded-lg border border-white/10 bg-[#0f172a]/60 backdrop-blur-md px-3 py-1.5 text-xs font-semibold text-slate-200 outline-none transition focus:border-white/20 focus:bg-white/10 cursor-pointer"
              >
                <option className="bg-[#0f172a]" value="price-asc">Price: Low to High</option>
                <option className="bg-[#0f172a]" value="price-desc">Price: High to Low</option>
                <option className="bg-[#0f172a]" value="time-asc">Time: Earliest</option>
                <option className="bg-[#0f172a]" value="time-desc">Time: Latest</option>
                <option className="bg-[#0f172a]" value="seats-desc">Seats Available</option>
              </select>
            </div>
          </div>

          {/* Results List */}
          <div className="flex flex-col gap-3">
            {processedResults.map((schedule) => (
              <button
                key={schedule.id}
                onClick={() => handleSelectSchedule(schedule)}
                className="glass-card flex flex-col md:flex-row md:items-center justify-between rounded-xl p-5 text-left border-white/5 gap-4"
              >
                {/* Operator Info */}
                <div className="flex flex-col gap-2.5">
                  <div className="flex items-center gap-2.5">
                    <TransportBadge type={schedule.operator.operator_type} />
                    <span className="font-bold text-white text-base">
                      {schedule.operator.operator_name}
                    </span>
                  </div>

                  {/* Route & Times */}
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex flex-col">
                      <span className="text-lg font-bold text-slate-100">{schedule.departure_time}</span>
                      <span className="text-xs text-slate-400">{schedule.route.departure_city}</span>
                    </div>

                    <div className="flex flex-col items-center px-4 w-28 relative">
                      <span className="text-[10px] text-slate-500 font-semibold mb-0.5 tracking-wider">
                        {formatDuration(schedule.route.estimated_duration_minutes)}
                      </span>
                      <div className="w-full h-[2px] bg-white/10 relative">
                        <div className="absolute right-0 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-orange-500" />
                      </div>
                      {schedule.route.distance_km && (
                        <span className="text-[9px] text-slate-500 font-medium mt-0.5">
                          {schedule.route.distance_km} km
                        </span>
                      )}
                    </div>

                    <div className="flex flex-col">
                      <span className="text-lg font-bold text-slate-100">{schedule.arrival_time}</span>
                      <span className="text-xs text-slate-400">{schedule.route.arrival_city}</span>
                    </div>
                  </div>
                </div>

                {/* Pricing & Seats */}
                <div className="flex flex-row md:flex-col items-center md:items-end justify-between border-t border-white/5 pt-3 md:border-t-0 md:pt-0 gap-2">
                  <div className="text-left md:text-right">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block mb-0.5">Price</span>
                    <span className="text-2xl font-extrabold text-orange-400">
                      Rs. {schedule.base_fare.toLocaleString()}
                    </span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">per seat</span>
                  </div>

                  <div className="text-right">
                    <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-semibold ${
                      schedule.available_seats > 10
                        ? "bg-emerald-500/10 text-emerald-300"
                        : "bg-amber-500/10 text-amber-300"
                    }`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${
                        schedule.available_seats > 10 ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
                      }`} />
                      {schedule.available_seats} / {schedule.total_seats} seats left
                    </span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
