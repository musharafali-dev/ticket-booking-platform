import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types/api";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  setAuth: (accessToken: string, refreshToken: string, user: User) => void;
  setUser: (user: User) => void;
  clearAuth: () => void;
}

/**
 * SECURITY TRADE-OFF (explicit, not accidental): tokens are persisted to
 * localStorage via Zustand's persist middleware. This is convenient (survives
 * page refresh without a re-login) but means a successful XSS on this
 * origin can exfiltrate the access AND refresh token, not just the access
 * token -- a stricter design would keep the refresh token only in an
 * httpOnly cookie set by the backend, invisible to any JS on the page
 * entirely.
 *
 * Accepted for this MVP because: (1) no third-party scripts are loaded,
 * shrinking the realistic XSS surface, (2) access tokens are short-lived
 * (30 min, see backend ACCESS_TOKEN_EXPIRE_MINUTES) limiting exposure
 * window, and (3) refresh tokens are already single-use/rotated
 * server-side (see backend app/auth/service.py::rotate_refresh_token),
 * so a stolen-and-used refresh token invalidates itself on next
 * legitimate use, surfacing the compromise rather than allowing silent
 * indefinite reuse.
 *
 * Flagged as a follow-up for a production hardening pass: move refresh
 * token issuance to an httpOnly, Secure, SameSite=strict cookie set
 * directly by the backend's /auth/login and /auth/refresh responses,
 * with the frontend never holding it in JS-readable storage at all.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setAuth: (accessToken, refreshToken, user) =>
        set({ accessToken, refreshToken, user }),
      setUser: (user) => set({ user }),
      clearAuth: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: "ticket-booking-auth" }
  )
);
