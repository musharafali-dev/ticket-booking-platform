import { create } from "zustand";
import type { PassengerInput, ScheduleSearchResult } from "@/types/api";

interface SelectedSeat {
  id: number;
  seat_number: string;
  price: number;
}

interface BookingFlowState {
  schedule: ScheduleSearchResult | null;
  selectedSeats: SelectedSeat[];
  passengers: PassengerInput[];
  contactEmail: string;
  contactPhone: string;

  setSchedule: (schedule: ScheduleSearchResult) => void;
  toggleSeat: (seat: SelectedSeat) => void;
  setPassengers: (passengers: PassengerInput[]) => void;
  setContactInfo: (email: string, phone: string) => void;
  reset: () => void;
}

/**
 * Deliberately NOT persisted to localStorage (unlike auth-store): this is
 * transient, single-session flow state. If a user refreshes mid-booking,
 * starting over is the correct, safe behavior -- seat locks are
 * time-boxed server-side (BOOKING_EXPIRATION_MINUTES) regardless of what
 * the client remembers, so persisting this client-side would just create
 * a confusing UI showing "selected" seats that may have already expired
 * or been taken by someone else server-side.
 */
export const useBookingFlowStore = create<BookingFlowState>((set) => ({
  schedule: null,
  selectedSeats: [],
  passengers: [],
  contactEmail: "",
  contactPhone: "",

  setSchedule: (schedule) => set({ schedule, selectedSeats: [] }),

  toggleSeat: (seat) =>
    set((state) => {
      const exists = state.selectedSeats.some((s) => s.id === seat.id);
      return {
        selectedSeats: exists
          ? state.selectedSeats.filter((s) => s.id !== seat.id)
          : [...state.selectedSeats, seat],
      };
    }),

  setPassengers: (passengers) => set({ passengers }),
  setContactInfo: (contactEmail, contactPhone) => set({ contactEmail, contactPhone }),

  reset: () =>
    set({
      schedule: null,
      selectedSeats: [],
      passengers: [],
      contactEmail: "",
      contactPhone: "",
    }),
}));
