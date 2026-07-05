"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { loginSchema, type LoginFormValues } from "@/lib/validation";
import { apiClient, ApiError } from "@/lib/api-client";
import type { TokenResponse, User } from "@/types/api";
import { useAuthStore } from "@/store/auth-store";
import { TextField } from "@/components/text-field";
import { Button } from "@/components/button";
import { Alert } from "@/components/alert";

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (values: LoginFormValues) => {
    setApiError(null);
    try {
      const tokens = await apiClient.post<TokenResponse>("/auth/login", values, {
        skipAuth: true,
      });
      const user = await apiClient.get<User>("/auth/me", {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      });
      setAuth(tokens.access_token, tokens.refresh_token, user);
      router.push("/");
    } catch (err) {
      setApiError(
        err instanceof ApiError ? err.detail : "Something went wrong. Please try again."
      );
    }
  };

  return (
    <div className="mx-auto max-w-md glass-panel rounded-2xl p-6 sm:p-8 border-white/5 shadow-2xl mt-8">
      <h1 className="mb-6 text-2xl font-extrabold text-white">Log in</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
        {apiError && <Alert variant="error">{apiError}</Alert>}

        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          {...register("email")}
          error={errors.email?.message}
        />
        <TextField
          label="Password"
          type="password"
          autoComplete="current-password"
          {...register("password")}
          error={errors.password?.message}
        />

        <Button type="submit" isLoading={isSubmitting} className="w-full mt-2 py-3">
          Log in
        </Button>
      </form>
    </div>
  );
}
