// Types mirror frontend/mock/openapi.yaml (pinned API contract v1, SAL 1).
// Field names/types are binding; the mock syncs with the canonical root spec (D5).

export interface Property {
  id: number;
  name: string;
  hotel_type: string;
  location_type: "lake" | "mountain";
  /** Assumed capacity (190/230), not measured. */
  room_count: number;
  ta_hotel_id: number | null;
}

export interface KpiSummary {
  property_id: number | null;
  date_from: string;
  date_to: string;
  valid_bookings: number;
  revenue: number;
  room_nights: number;
  adr: number;
  cancellation_rate: number;
  /** 0-1 ratio against assumed capacity, not measured. */
  occupancy_avg: number;
  /** Against assumed capacity, not measured. */
  revpar: number;
}

export interface KpiDailyPoint {
  date: string;
  room_nights: number;
  revenue: number;
  /** 0-1 ratio against assumed capacity. */
  occupancy: number;
  /** null on zero-activity days. */
  adr: number | null;
  revenue_per_available_room: number;
}

export interface ChannelMixItem {
  market_segment: string;
  bookings: number;
  revenue: number;
  share: number;
}

export interface SeasonalityPoint {
  month: number;
  avg_adr: number;
  avg_occupancy: number;
  avg_revenue: number;
}

export interface ReviewSummary {
  property_id: number | null;
  count: number;
  overall: number;
  cleanliness: number;
  value: number;
  location: number;
  rooms: number;
  sleep_quality: number;
}

export interface Review {
  id: number;
  property_id: number;
  ta_hotel_id: number;
  post_date: string;
  stay_year: number | null;
  overall: number | null;
  cleanliness: number | null;
  value: number | null;
  location: number | null;
  rooms: number | null;
  sleep_quality: number | null;
  title: string | null;
  body: string | null;
  lang: string | null;
}

export interface Booking {
  id: number;
  property_id: number;
  arrival_date: string;
  nights: number;
  adr: number;
  is_canceled: boolean;
  adults: number;
  children: number;
  babies: number;
  country: string | null;
  customer_type: string;
  market_segment: string;
  distribution_channel: string;
  deposit_type: string;
  lead_time: number;
}

export interface GuestRequest {
  id: number;
  property_id: number;
  received_at: string;
  body: string;
  /** Assistant output; null until D15. */
  category: string | null;
  /** Assistant output; null until D15. */
  draft_reply: string | null;
  status: "new" | "draft" | "sent";
}

export interface GuestRequestUpdate {
  status?: "new" | "draft" | "sent";
  draft_reply?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  role: string;
}

export interface PageMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface Page<T> {
  data: T[];
  meta: PageMeta;
}

export interface DataEnvelope<T> {
  data: T;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}