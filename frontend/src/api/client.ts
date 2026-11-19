import type {
  ApiErrorBody,
  DataEnvelope,
  KpiDailyPoint,
  KpiSummary,
  LoginResponse,
  Page,
  Property,
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

// Demo token from /api/auth/login; real JWT issuance is D11.
let token: string | null = null;

// evento lanciato quando l'api risponde 401: la pagina torna al login
export const SESSION_EXPIRED = "buby:session-expired";

// rimette il token salvato (ricarica pagina) o lo toglie (logout)
export function setToken(value: string | null) {
  token = value;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!token && path !== "/api/auth/login") {
    await login("manager@buby.travel", "demo");
  }
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