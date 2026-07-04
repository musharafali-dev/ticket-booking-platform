"use client";

import Link from "next/link";
import { useAuthStore } from "@/store/auth-store";

export function NavBar() {
  const { user, clearAuth } = useAuthStore();

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <Link href="/" className="text-lg font-bold text-brand-600">
          TicketBooking<span className="text-slate-900">.pk</span>
        </Link>

        <nav className="flex items-center gap-4 text-sm">
          <Link href="/" className="text-slate-600 hover:text-slate-900">
            Search
          </Link>
          {user ? (
            <>
              <Link href="/bookings" className="text-slate-600 hover:text-slate-900">
                My Bookings
              </Link>
              <Link href="/profile" className="text-slate-600 hover:text-slate-900">
                {user.first_name}
              </Link>
              <button
                onClick={clearAuth}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-slate-700 hover:bg-slate-50"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-slate-600 hover:text-slate-900">
                Log in
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-brand-600 px-3 py-1.5 text-white hover:bg-brand-700"
              >
                Sign up
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
