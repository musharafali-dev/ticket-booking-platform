import type { ApiErrorBody } from "@/types/api";
import { useAuthStore } from "@/store/auth-store";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/**
 * Thrown on any non-2xx response. Carries the parsed FastAPI error detail
 * (not just the HTTP status) so callers can show the actual validation or
 * business-rule message the backend produced -- e.g. "Seats unavailable"
 * or the 409 conflict message from a race lost against another user,
 * rather than a generic "Something went wrong."
 */
export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function extractDetail(body: ApiErrorBody | undefined, fallback: string): string {
  if (!body?.detail) return fallback;
  if (typeof body.detail === "string") return body.detail;
  // Pydantic validation errors come back as a list of {msg, loc} objects.
  return body.detail.map((d) => d.msg).join("; ");
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Skip attaching the Authorization header, for public endpoints. */
  skipAuth?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, skipAuth, headers, ...rest } = options;

  const finalHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(headers as Record<string, string> | undefined),
  };

  if (!skipAuth) {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      finalHeaders["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: finalHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let parsedBody: ApiErrorBody | undefined;
    try {
      parsedBody = await response.json();
    } catch {
      // Response body wasn't JSON (e.g. a raw 502 from a proxy) -- fall
      // through to the generic message below rather than throwing here.
    }
    throw new ApiError(
      response.status,
      extractDetail(parsedBody, `Request failed with status ${response.status}`)
    );
  }

  // 204 No Content and similar have no body to parse.
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
};

/** SWR fetcher: SWR calls this with just the key (the path). */
export const swrFetcher = <T,>(path: string): Promise<T> => apiClient.get<T>(path);
