"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { registerSchema, type RegisterFormValues } from "@/lib/validation";
import { apiClient, ApiError } from "@/lib/api-client";
import type { User } from "@/types/api";
import { TextField } from "@/components/text-field";
import { Button } from "@/components/button";
import { Alert } from "@/components/alert";

export default function RegisterPage() {
  const router = useRouter();
  const [apiError, setApiError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({ resolver: zodResolver(registerSchema) });

  const onSubmit = async (values: RegisterFormValues) => {
    setApiError(null);
    try {
      await apiClient.post<User>("/auth/register", values, { skipAuth: true });
      setSuccess(true);
      setTimeout(() => router.push("/login"), 2500);
    } catch (err) {
      setApiError(err instanceof ApiError ? err.detail : "Something went wrong. Please try again.");
    }
  };

  if (success) {
    return (
      <div className="mx-auto max-w-md">
        <Alert variant="success">
          Account created! Check your email (or, in local dev, the backend
          server logs) for a verification link. Redirecting you to log in…
        </Alert>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md glass-panel rounded-2xl p-6 sm:p-8 border-white/5 shadow-2xl mt-8">
      <h1 className="mb-6 text-2xl font-extrabold text-white">Create account</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
        {apiError && <Alert variant="error">{apiError}</Alert>}

        <div className="grid grid-cols-2 gap-4">
          <TextField label="First name" {...register("first_name")} error={errors.first_name?.message} />
          <TextField label="Last name" {...register("last_name")} error={errors.last_name?.message} />
        </div>

        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          {...register("email")}
          error={errors.email?.message}
        />

        <TextField
          label="Phone number (optional)"
          placeholder="+92-300-1234567"
          {...register("phone_number")}
          error={errors.phone_number?.message}
        />

        <TextField
          label="Password"
          type="password"
          autoComplete="new-password"
          {...register("password")}
          error={errors.password?.message}
        />
        <p className="-mt-3 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          Must contain 8+ chars, 1 uppercase, 1 digit, 1 symbol.
        </p>

        <Button type="submit" isLoading={isSubmitting} className="w-full mt-2 py-3">
          Create Account
        </Button>
      </form>
    </div>
  );
}
