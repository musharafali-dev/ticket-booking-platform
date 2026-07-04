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
      <h1 className="mb-6 text-2xl font-bold text-slate-900">Profile</h1>
      <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-6">
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
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className="text-sm text-slate-900">{value}</p>
    </div>
  );
}
