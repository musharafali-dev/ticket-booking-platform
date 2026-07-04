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
    <div className="mx-auto max-w-md">
      <h1 className="mb-6 text-2xl font-bold text-slate-900">Create your account</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
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
        <p className="-mt-2 text-xs text-slate-500">
          At least 8 characters, one uppercase letter, one digit, one special character.
        </p>

        <Button type="submit" isLoading={isSubmitting}>
          Create account
        </Button>
      </form>
    </div>
  );
}
