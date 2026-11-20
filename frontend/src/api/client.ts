import type {
  ApiErrorBody,
  Booking,
  DataEnvelope,
  GuestRequest,
  GuestRequestUpdate,
  KpiDailyPoint,
  KpiSummary,
  LoginResponse,
  Page,
  Property,
  Review,
  ReviewSummary,
} from "./types";

const BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:4010";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: Record<string, unknown> | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Bearer JWT from POST /api/auth/login (D11); null until Login.tsx signs in.
let token: string | null = null;

// evento lanciato quando l'api risponde 401: la pagina torna al login
export const SESSION_EXPIRED = "buby:session-expired";

// rimette il token salvato (ricarica pagina) o lo toglie (logout)
export function setToken(value: string | null) {
  token = value;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });
  const body: unknown = await res.json().catch(() => null);
  // token scaduto o non valido: si torna al login (vedi AuthGate.tsx)
  if (res.status === 401 && path !== "/api/auth/login") {
    token = null;
    if (typeof window !== "undefined") window.dispatchEvent(new Event(SESSION_EXPIRED));
  }
  if (!res.ok) {
    const error = (body as { error?: ApiErrorBody } | null)?.error;
    throw new ApiError(
      res.status,
      error?.code ?? "http_error",
      error?.message ?? res.statusText,
      error?.details,
    );
  }
  return body as T;
}

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  const result = await request<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  token = result.access_token;
  return result;
}

export type KpiQuery = {
  property_id?: number | null;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
};

function queryString(params: KpiQuery): string {
  const entries = Object.entries(params).filter(
    ([, value]) => value !== undefined && value !== null && value !== "",
  );
  return entries.length ? `?${new URLSearchParams(entries.map(([k, v]) => [k, String(v)]))}` : "";
}

export async function getProperties(): Promise<Property[]> {
  const envelope = await request<DataEnvelope<Property[]>>("/api/properties");
  return envelope.data;
}

export function getKpiSummary(params: KpiQuery): Promise<KpiSummary> {
  return request<KpiSummary>(`/api/kpis/summary${queryString(params)}`);
}

export function getKpiDaily(params: KpiQuery): Promise<Page<KpiDailyPoint>> {
  return request<Page<KpiDailyPoint>>(`/api/kpis/daily${queryString(params)}`);
}

// /api/reviews/summary — property_id only; response is the ReviewSummary directly (no envelope)
export function getReviewSummary(params: {
  property_id?: number | null;
}): Promise<ReviewSummary> {
  return request<ReviewSummary>(`/api/reviews/summary${queryString(params)}`);
}

// /api/reviews — paginated; structurally assignable to KpiQuery so queryString works
export function listReviews(params: {
  property_id?: number | null;
  page?: number;
  page_size?: number;
}): Promise<Page<Review>> {
  return request<Page<Review>>(`/api/reviews${queryString(params)}`);
}

// /api/bookings — declared filters per spec (is_canceled boolean serialised via String())
export type BookingQuery = {
  property_id?: number | null;
  date_from?: string;
  date_to?: string;
  is_canceled?: boolean;
  market_segment?: string;
  page?: number;
  page_size?: number;
};

export function listBookings(params: BookingQuery): Promise<Page<Booking>> {
  return request<Page<Booking>>(`/api/bookings${queryString(params)}`);
}

// /api/guest-requests — paginated, optional status filter
export type GuestRequestQuery = {
  property_id?: number | null;
  status?: "new" | "draft" | "sent";
  page?: number;
  page_size?: number;
};

export function listGuestRequests(params: GuestRequestQuery): Promise<Page<GuestRequest>> {
  return request<Page<GuestRequest>>(`/api/guest-requests${queryString(params)}`);
}

// PATCH /api/guest-requests/{id} — returns GuestRequest directly (no envelope).
// Role matrix: admin/manager only; property_manager receives 403 Forbidden.
export function patchGuestRequest(
  id: number,
  update: GuestRequestUpdate,
): Promise<GuestRequest> {
  return request<GuestRequest>(`/api/guest-requests/${id}`, {
    method: "PATCH",
    body: JSON.stringify(update),
  });
}