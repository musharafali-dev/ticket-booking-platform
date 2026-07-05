"use client";

import { useAuthStore } from "@/store/auth-store";
import { Alert } from "@/components/alert";

/**
 * Deliberately minimal for this MVP: displays the current user's basic
 * info, no editing. Full profile management (address book, payment
 * methods, notification preferences -- all present in the backend schema
 * but not yet exposed via API endpoints) is scoped out per the agreed
 * 2-day priority: core booking flow first, profile as a stub.
 */
export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);

  if (!user) {
    return <Alert variant="info">Please log in to view your profile.</Alert>;
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mb-6 text-2xl font-extrabold text-white">Profile</h1>
      <div className="flex flex-col gap-5 rounded-2xl glass-panel p-6 border-white/5 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b from-blue-500 to-indigo-500" />
        <Field label="Name" value={`${user.first_name} ${user.last_name}`} />
        <Field label="Email" value={user.email} />
        <Field label="Phone" value={user.phone_number ?? "Not provided"} />
        <Field
          label="Email verified"
          value={user.is_email_verified ? "Yes" : "No — check your inbox for a verification link"}
        />
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-b border-white/5 pb-3 last:border-b-0 last:pb-0">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">{label}</p>
      <p className="text-sm font-semibold text-slate-200">{value}</p>
    </div>
  );
}
