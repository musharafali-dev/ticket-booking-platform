import useSWR from "swr";
import type { ScheduleSearchResult } from "@/types/api";

interface SearchParams {
  departureCity: string;
  arrivalCity: string;
  departureDate: string;
  transportType?: string;
}

/**
 * Returns null as the key (disabling the fetch) until all required fields
 * are present -- SWR's documented pattern for conditional fetching. This
 * avoids firing a request with empty query params on initial render before
 * the user has filled in the form.
 */
export function useScheduleSearch(params: SearchParams | null) {
  const key = params
    ? `/search/schedules?departure_city=${encodeURIComponent(params.departureCity)}` +
      `&arrival_city=${encodeURIComponent(params.arrivalCity)}` +
      `&departure_date=${params.departureDate}` +
      (params.transportType ? `&transport_type=${params.transportType}` : "")
    : null;

  return useSWR<ScheduleSearchResult[]>(key);
}
