import useSWR from "swr";
import type { ScheduleDetail } from "@/types/api";

/**
 * Polls every 10s while the seat-selection screen is mounted. This is the
 * concrete payoff of choosing SWR over a plain fetch wrapper: a seat can be
 * taken by another user at any moment (see the booking concurrency
 * guarantee backend/app/booking/service.py lock_seats function), and without
 * this poll a user could stare at a seat map showing a seat as "available"
 * for minutes after someone else has already locked it, only discovering
 * the conflict when their own booking attempt gets rejected with a 409.
 *
 * 10s is a compromise: frequent enough to catch most conflicts before
 * checkout, not so frequent it meaningfully increases backend load for an
 * MVP's expected traffic. Revisit if/when real usage data suggests a
 * different interval is warranted.
 */
export function useScheduleDetail(scheduleId: number | null) {
  return useSWR<ScheduleDetail>(
    scheduleId !== null ? `/search/schedules/${scheduleId}` : null,
    { refreshInterval: 10_000 }
  );
}
