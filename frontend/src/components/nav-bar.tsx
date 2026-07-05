"use client";

import Link from "next/link";
import { useAuthStore } from "@/store/auth-store";
import { usePathname } from "next/navigation";
import clsx from "clsx";

export function NavBar() {
  const { user, clearAuth } = useAuthStore();
  const pathname = usePathname();

  const isLinkActive = (path: string) => pathname === path;

  return (
    <div className="mx-auto max-w-5xl px-4 pt-4">
      <header className="rounded-xl border border-white/5 bg-[#0f172a]/60 backdrop-blur-md px-6 py-4 shadow-xl">
        <div className="flex items-center justify-between">
          <Link href="/" className="group text-lg font-extrabold tracking-tight">
            <span className="bg-gradient-to-r from-orange-400 to-amber-400 bg-clip-text text-transparent group-hover:from-orange-300 group-hover:to-amber-300 transition-all duration-300">
              TicketBooking
            </span>
            <span className="text-slate-200">.pk</span>
          </Link>

          <nav className="flex items-center gap-6 text-sm font-medium">
            <Link
              href="/"
              className={clsx(
                "transition duration-200",
                isLinkActive("/")
                  ? "text-orange-400"
                  : "text-slate-300 hover:text-white"
              )}
            >
              Search
            </Link>
            <Link
              href="/schedules"
              className={clsx(
                "transition duration-200",
                isLinkActive("/schedules")
                  ? "text-orange-400"
                  : "text-slate-300 hover:text-white"
              )}
            >
              Schedules
            </Link>
            {user ? (
              <>
                <Link
                  href="/bookings"
                  className={clsx(
                    "transition duration-200",
                    isLinkActive("/bookings")
                      ? "text-orange-400"
                      : "text-slate-300 hover:text-white"
                  )}
                >
                  My Bookings
                </Link>
                <Link
                  href="/profile"
                  className={clsx(
                    "transition duration-200",
                    isLinkActive("/profile")
                      ? "text-orange-400"
                      : "text-slate-300 hover:text-white"
                  )}
                >
                  {user.first_name}
                </Link>
                <button
                  onClick={clearAuth}
                  className="rounded-lg border border-white/10 px-3.5 py-1.5 text-slate-300 transition duration-200 hover:bg-white/5 hover:border-white/20 hover:text-white"
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className={clsx(
                    "transition duration-200",
                    isLinkActive("/login")
                      ? "text-orange-400"
                      : "text-slate-300 hover:text-white"
                  )}
                >
                  Log in
                </Link>
                <Link
                  href="/register"
                  className="rounded-lg bg-gradient-to-r from-orange-500 to-amber-500 px-4 py-2 font-semibold text-white shadow-[0_4px_15px_rgba(249,115,22,0.2)] hover:from-orange-400 hover:to-amber-400 transition duration-300"
                >
                  Sign up
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>
    </div>
  );
}
