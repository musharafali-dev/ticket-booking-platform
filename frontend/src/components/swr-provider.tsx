"use client";

import { SWRConfig } from "swr";
import { swrFetcher } from "@/lib/api-client";

/**
 * Global SWR config. refreshInterval is set per-hook where it matters
 * (seat availability while a user is actively choosing seats) rather than
 * globally -- polling every list/detail endpoint on a fixed interval would
 * waste requests on data that rarely changes (e.g. city lists) and isn't
 * a good default for a booking platform where most reads are one-shot.
 */
export function SwrProvider({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher: swrFetcher,
        revalidateOnFocus: true,
        shouldRetryOnError: false,
      }}
    >
      {children}
    </SWRConfig>
  );
}
