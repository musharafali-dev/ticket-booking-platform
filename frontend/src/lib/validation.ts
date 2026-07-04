import { z } from "zod";

/**
 * Mirrors backend/app/auth/schemas.py::UserRegister.password_strength exactly
 * (uppercase + digit + special char, min 8 chars) so the user gets instant
 * client-side feedback instead of discovering the rule only after a round
 * trip to the API. The backend re-validates independently regardless --
 * this is a UX improvement, never a substitute for server-side validation.
 */
export const registerSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
    .regex(/[0-9]/, "Password must contain at least one digit")
    .regex(/[^A-Za-z0-9]/, "Password must contain at least one special character"),
  first_name: z.string().min(1, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
  phone_number: z.string().optional(),
});

export type RegisterFormValues = z.infer<typeof registerSchema>;

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export const passengerSchema = z.object({
  first_name: z.string().min(1, "Required"),
  last_name: z.string().min(1, "Required"),
  id_type: z.string().optional(),
  id_number: z.string().optional(),
});

export const contactSchema = z.object({
  contact_email: z.string().email("Enter a valid email address"),
  contact_phone: z.string().optional(),
});
