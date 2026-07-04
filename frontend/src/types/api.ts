/**
 * Types mirroring backend Pydantic schemas (see backend app schemas
 * under each feature module's schemas.py file).
 *
 * Kept as plain interfaces, hand-synced with the backend rather than
 * codegen'd from the OpenAPI schema. For a 2-day MVP with one developer
 * on both ends, codegen tooling (openapi-typescript, etc.) is more setup
 * cost than the type-drift risk it prevents — flagged as a reasonable
 * follow-up once the API surface stabilizes and/or a second developer
 * joins, at which point drift risk rises sharply.
 */

export type UserRole = "CUSTOMER" | "OPERATOR" | "ADMIN";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string | null;
  role: UserRole;
  is_email_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type TransportType = "BUS" | "TRAIN" | "AIRPLANE";
export type ScheduleStatus = "SCHEDULED" | "CANCELLED" | "COMPLETED";
export type SeatStatus = "AVAILABLE" | "LOCKED" | "BOOKED" | "BLOCKED";
export type BookingStatus = "PENDING" | "CONFIRMED" | "CANCELLED" | "EXPIRED";
export type PaymentStatus =
  | "PENDING"
  | "PROCESSING"
  | "COMPLETED"
  | "FAILED"
  | "REFUNDED";

export interface OperatorSummary {
  id: number;
  operator_name: string;
  operator_type: TransportType;
}

export interface RouteSummary {
  id: number;
  route_code: string;
  departure_city: string;
  arrival_city: string;
  distance_km: number | null;
  estimated_duration_minutes: number | null;
}

export interface ScheduleSearchResult {
  id: number;
  departure_date: string;
  departure_time: string;
  arrival_time: string;
  base_fare: number;
  available_seats: number;
  total_seats: number;
  status: ScheduleStatus;
  operator: OperatorSummary;
  route: RouteSummary;
}

export interface SeatDetail {
  id: number;
  seat_number: string;
  seat_category: string;
  status: SeatStatus;
  price: number;
}

export interface ScheduleDetail extends ScheduleSearchResult {
  seats: SeatDetail[];
}

export interface PassengerInput {
  seat_id: number;
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  id_type?: string;
  id_number?: string;
}

export interface BookingCreateRequest {
  schedule_id: number;
  passengers: PassengerInput[];
  contact_email: string;
  contact_phone?: string;
}

export interface PassengerResponse {
  id: number;
  first_name: string;
  last_name: string;
  seat_number: string;
}

export interface Booking {
  id: number;
  booking_code: string;
  number_of_passengers: number;
  total_amount: number;
  status: BookingStatus;
  payment_status: PaymentStatus;
  contact_email: string;
  expires_at: string;
  created_at: string;
  passengers: PassengerResponse[];
}

export interface PaymentInitiateResponse {
  payment_reference: string;
  redirect_url: string | null;
  requires_redirect: boolean;
  status: PaymentStatus;
}

/** Shape of FastAPI's default error response body. */
export interface ApiErrorBody {
  detail: string | { msg: string; loc: (string | number)[] }[];
}
