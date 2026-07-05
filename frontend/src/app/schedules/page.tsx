"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { TransportBadge } from "@/components/transport-badge";
import { Button } from "@/components/button";
import { Alert } from "@/components/alert";
import { useBookingFlowStore } from "@/store/booking-flow-store";
import type { ScheduleSearchResult, TransportType } from "@/types/api";

function todayIsoDate(): string {
  return new Date().toISOString().split("T")[0] ?? "";
}

function formatDuration(minutes: number | null): string {
  if (!minutes) return "N/A";
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
}

export default function SchedulesDirectoryPage() {
  const router = useRouter();
  const setSchedule = useBookingFlowStore((s) => s.setSchedule);

  const [activeTab, setActiveTab] = useState<TransportType>("AIRPLANE");
  const [selectedDate, setSelectedDate] = useState(todayIsoDate());
  const [depFilter, setDepFilter] = useState("");
  const [arrFilter, setArrFilter] = useState("");

  // Fetch all cities for autocomplete dropdowns
  const { data: cities } = useSWR<string[]>("/search/cities");

  // Fetch all schedules for the selected date and type
  const { data: schedules, error, isLoading } = useSWR<ScheduleSearchResult[]>(
    `/search/all-schedules?departure_date=${selectedDate}&transport_type=${activeTab}`
  );

  const handleBookNow = (schedule: ScheduleSearchResult) => {
    setSchedule(schedule);
    router.push(`/schedules/${schedule.id}/seats`);
  };

  // Client-side filtering by departure and arrival cities
  const filteredSchedules = schedules
    ? schedules.filter((s: ScheduleSearchResult) => {
        const matchesDep = depFilter
          ? s.route.departure_city.toLowerCase() === depFilter.toLowerCase()
          : true;
        const matchesArr = arrFilter
          ? s.route.arrival_city.toLowerCase() === arrFilter.toLowerCase()
          : true;
        return matchesDep && matchesArr;
      })
    : [];

  return (
    <div className="flex flex-col gap-8 max-w-4xl mx-auto">
      {/* Title Header */}
      <div className="text-center py-4">
        <h1 className="mb-2 text-4xl font-extrabold tracking-tight bg-gradient-to-r from-orange-400 via-amber-200 to-indigo-400 bg-clip-text text-transparent">
          Schedules Directory
        </h1>
        <p className="text-slate-400 text-sm max-w-md mx-auto">
          Explore complete routes, timings, and prices for all flights, buses, and trains.
        </p>
      </div>

      {/* Mode Module Cards */}
      <div className="grid grid-cols-3 gap-4">
        {[
          {
            type: "AIRPLANE" as TransportType,
            label: "Flights",
            desc: "PIA, AirSial, Airblue",
            icon: (
              <svg className="w-6 h-6 text-sky-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L6 12Zm0 0h7.5" />
              </svg>
            ),
          },
          {
            type: "BUS" as TransportType,
            label: "Buses",
            desc: "Daewoo, Faisal Movers, Bilal Travels",
            icon: (
              <svg className="w-6 h-6 text-amber-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 18.75a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0ZM7.5 18.75a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0ZM2.25 15h19.5M3 18.75h18M4.5 5.25h15a2.25 2.25 0 0 1 2.25 2.25v7.5a2.25 2.25 0 0 1-2.25 2.25h-15A2.25 2.25 0 0 1 2.25 15v-7.5A2.25 2.25 0 0 1 4.5 5.25Zm0 4.5h15v-1.5h-15v1.5Zm0 3.75h15v-1.5h-15v1.5Z" />
              </svg>
            ),
          },
          {
            type: "TRAIN" as TransportType,
            label: "Trains",
            desc: "Pak Railways, Tezgam, Green Line",
            icon: (
              <svg className="w-6 h-6 text-purple-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5.25 19.5h13.5M5.25 4.5h13.5m-10.5 3h7.5m-7.5 3h7.5m-7.5 3h7.5M5.25 4.5A2.25 2.25 0 0 0 3 6.75v10.5A2.25 2.25 0 0 0 5.25 19.5M18.75 4.5A2.25 2.25 0 0 1 21 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25M6 19.5l-1.5 3m13.5-3 1.5 3" />
              </svg>
            ),
          },
        ].map((tab) => (
          <button
            key={tab.type}
            onClick={() => setActiveTab(tab.type)}
            className={`glass-card p-5 text-left rounded-2xl flex flex-col items-start border ${
              activeTab === tab.type
                ? "border-orange-500/35 bg-orange-500/[0.04] shadow-[0_4px_25px_rgba(249,115,22,0.15)]"
                : "border-white/5 hover:border-white/10"
            }`}
          >
            {tab.icon}
            <span className="font-bold text-lg text-white mb-0.5">{tab.label}</span>
            <span className="text-[10px] text-slate-400 leading-normal font-medium">{tab.desc}</span>
          </button>
        ))}
      </div>

      {/* Filters Module */}
      <div className="glass-panel rounded-2xl p-6 border-white/5 flex flex-col md:flex-row gap-5 items-end">
        {/* Date Filter */}
        <div className="flex flex-col gap-1.5 w-full md:w-1/4">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-400">Date</label>
          <input
            type="date"
            min={todayIsoDate()}
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="glass-input rounded-lg px-4 py-3 text-sm focus:ring-0 focus:outline-none [color-scheme:dark] w-full"
          />
        </div>

        {/* Departure City Filter */}
        <div className="flex flex-col gap-1.5 w-full md:w-1/3">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-400">Departure City</label>
          <select
            value={depFilter}
            onChange={(e) => setDepFilter(e.target.value)}
            className="glass-input rounded-lg px-4 py-3 text-sm focus:ring-0 focus:outline-none w-full cursor-pointer"
          >
            <option className="bg-[#0f172a]" value="">All Departure Cities</option>
            {cities?.map((city: string) => (
              <option key={city} className="bg-[#0f172a]" value={city}>{city}</option>
            ))}
          </select>
        </div>

        {/* Arrival City Filter */}
        <div className="flex flex-col gap-1.5 w-full md:w-1/3">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-400">Arrival City</label>
          <select
            value={arrFilter}
            onChange={(e) => setArrFilter(e.target.value)}
            className="glass-input rounded-lg px-4 py-3 text-sm focus:ring-0 focus:outline-none w-full cursor-pointer"
          >
            <option className="bg-[#0f172a]" value="">All Arrival Cities</option>
            {cities?.map((city: string) => (
              <option key={city} className="bg-[#0f172a]" value={city}>{city}</option>
            ))}
          </select>
        </div>

        {/* Clear Filters Button */}
        {(depFilter || arrFilter) && (
          <button
            onClick={() => {
              setDepFilter("");
              setArrFilter("");
            }}
            className="text-xs font-bold text-orange-400 hover:text-orange-300 transition py-3"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Schedules List */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center gap-3 py-16" role="status">
          <svg className="h-8 w-8 animate-spin text-orange-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-slate-400 font-medium animate-pulse">Loading schedules...</p>
        </div>
      )}

      {error && <Alert variant="error">Could not load schedules. Please try again later.</Alert>}

      {!isLoading && !error && filteredSchedules.length === 0 && (
        <Alert variant="info">
          No schedules found matching your filter selection. Try changing the date or clearing filters.
        </Alert>
      )}

      {filteredSchedules.length > 0 && (
        <div className="flex flex-col gap-3">
          {filteredSchedules.map((schedule: ScheduleSearchResult) => (
            <div
              key={schedule.id}
              className="glass-panel flex flex-col md:flex-row md:items-center justify-between rounded-xl p-5 border-white/5 gap-4"
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

              {/* Pricing, Seats & Book Button */}
              <div className="flex flex-row md:flex-col items-center md:items-end justify-between border-t border-white/5 pt-3 md:border-t-0 md:pt-0 gap-4 w-full md:w-auto">
                <div className="text-left md:text-right">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block mb-0.5">Fare</span>
                  <span className="text-2xl font-extrabold text-orange-400">
                    Rs. {schedule.base_fare.toLocaleString()}
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    schedule.available_seats > 15
                      ? "bg-emerald-500/10 text-emerald-300"
                      : "bg-amber-500/10 text-amber-300"
                  }`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${
                      schedule.available_seats > 15 ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
                    }`} />
                    {schedule.available_seats} left
                  </span>

                  <Button onClick={() => handleBookNow(schedule)} className="py-2.5">
                    Book Seats
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
