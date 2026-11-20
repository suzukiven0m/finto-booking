import { beforeEach, describe, expect, it, vi } from "vitest";

// Fresh module per test so the cached bearer token does not leak between tests.
async function freshClient() {
  vi.resetModules();
  return import("./client");
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const loginBody = {
  access_token: "demo-token",
  token_type: "bearer",
  role: "manager",
};

const summaryBody = {
  property_id: null,
  date_from: "2015-07-01",
  date_to: "2017-08-31",
  valid_bookings: 61777,
  revenue: 22976960.13,
  room_nights: 218410,
  adr: 105.2,
  cancellation_rate: 0.2749,
  occupancy_avg: 0.6558,
  revpar: 68.99,
};

beforeEach(() => {
  vi.unstubAllGlobals();
});

// D11/WP7 adaptation: the client no longer auto-logs-in on secured calls.
// The three original tests now log in explicitly first (the Login.tsx flow),
// then assert the same fetch count, URLs, bearer header and envelopes.
describe("api client", () => {
  it("logs in and sends the bearer token on secured calls", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(loginBody))
      .mockResolvedValueOnce(jsonResponse(summaryBody));
    vi.stubGlobal("fetch", fetchMock);
    const { login, getKpiSummary } = await freshClient();

    await login("manager@buby.travel", "demo");
    const summary = await getKpiSummary({
      property_id: null,
      date_from: "2015-07-01",
      date_to: "2017-08-31",
    });

    expect(summary).toEqual(summaryBody);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const [loginUrl, loginInit] = fetchMock.mock.calls[0];
    expect(loginUrl).toBe("http://localhost:8000/api/auth/login");
    expect(loginInit.method).toBe("POST");
    const [summaryUrl, summaryInit] = fetchMock.mock.calls[1];
    // null property_id (both properties) is omitted from the query string
    expect(summaryUrl).toBe(
      "http://localhost:8000/api/kpis/summary?date_from=2015-07-01&date_to=2017-08-31",
    );
    expect(summaryInit.headers.Authorization).toBe("Bearer demo-token");
  });

  it("unwraps the {data,meta} envelope of paginated endpoints", async () => {
    const page = {
      data: [
        {
          date: "2016-11-04",
          room_nights: 0,
          revenue: 0,
          occupancy: 0,
          adr: null,
          revenue_per_available_room: 0,
        },
      ],
      meta: { page: 1, page_size: 50, total: 793, total_pages: 16 },
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(loginBody))
      .mockResolvedValueOnce(jsonResponse(page));
    vi.stubGlobal("fetch", fetchMock);
    const { login, getKpiDaily } = await freshClient();

    await login("manager@buby.travel", "demo");
    const result = await getKpiDaily({ property_id: 1, page_size: 200 });

    expect(result.meta.total).toBe(793);
    expect(result.data[0].adr).toBeNull();
    expect(fetchMock.mock.calls[1][0]).toBe(
      "http://localhost:8000/api/kpis/daily?property_id=1&page_size=200",
    );
  });

  it("throws ApiError with code/message from the {error} envelope", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(loginBody))
      .mockResolvedValueOnce(
        jsonResponse(
          {
            error: {
              code: "validation_error",
              message: "Request validation failed.",
              details: { property_id: "must be one of [1, 2]" },
            },
          },
          422,
        ),
      );
    vi.stubGlobal("fetch", fetchMock);
    const { login, getKpiSummary, ApiError } = await freshClient();

    await login("manager@buby.travel", "demo");
    const promise = getKpiSummary({ property_id: 3 });
    await expect(promise).rejects.toBeInstanceOf(ApiError);
    await expect(promise).rejects.toMatchObject({
      status: 422,
      code: "validation_error",
      message: "Request validation failed.",
    });
  });

  // WP3-mandated (P1): 401 outside login clears the token and fires the event
  it("clears the token and dispatches SESSION_EXPIRED on 401 outside login", async () => {
    const dispatchEvent = vi.fn();
    vi.stubGlobal("window", { dispatchEvent });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(loginBody))
      .mockResolvedValueOnce(
        jsonResponse(
          { error: { code: "unauthorized", message: "Missing or invalid bearer token." } },
          401,
        ),
      )
      .mockResolvedValueOnce(jsonResponse(summaryBody));
    vi.stubGlobal("fetch", fetchMock);
    const { login, getKpiSummary, SESSION_EXPIRED, ApiError } = await freshClient();

    await login("manager@buby.travel", "demo");
    await expect(getKpiSummary({})).rejects.toBeInstanceOf(ApiError);
    expect(dispatchEvent).toHaveBeenCalledTimes(1);
    expect(dispatchEvent.mock.calls[0][0].type).toBe(SESSION_EXPIRED);

    // token cleared: the next secured call goes out without Authorization
    await getKpiSummary({});
    expect(fetchMock.mock.calls[2][1].headers.Authorization).toBeUndefined();
  });

  it("does not dispatch SESSION_EXPIRED when login itself returns 401", async () => {
    const dispatchEvent = vi.fn();
    vi.stubGlobal("window", { dispatchEvent });
    const fetchMock = vi.fn().mockResolvedValueOnce(
      jsonResponse(
        { error: { code: "invalid_credentials", message: "Email or password is incorrect." } },
        401,
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { login, ApiError } = await freshClient();

    await expect(login("manager@buby.travel", "wrong")).rejects.toBeInstanceOf(ApiError);
    expect(dispatchEvent).not.toHaveBeenCalled();
  });
});

// WP11: D13/D19/D20 client functions — URL construction, envelope parsing,
// error propagation and PATCH body. Component tests are skipped: vitest runs
// in "node" environment (vite.config.ts test.environment=node) with no DOM;
// jsdom/happy-dom are not installed and not needed per the task contract.
describe("D13 / D19 / D20 api client functions", () => {
  const loginBody = {
    access_token: "demo-token",
    token_type: "bearer",
    role: "manager",
  };

  it("getReviewSummary — builds correct URL and returns ReviewSummary directly", async () => {
    const summaryBody = {
      property_id: 1,
      count: 762,
      overall: 3.86,
      cleanliness: 4.11,
      value: 3.43,
      location: 4.62,
      rooms: 3.78,
      sleep_quality: 4.17,
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(loginBody))
      .mockResolvedValueOnce(jsonResponse(summaryBody));
    vi.stubGlobal("fetch", fetchMock);
    const { login, getReviewSummary } = await freshClient();

    await login("manager@buby.travel", "demo");
    const result = await getReviewSummary({ property_id: 1 });

    expect(result).toEqual(summaryBody);
    expect(fetchMock.mock.calls[1][0]).toBe(
      "http://localhost:8000/api/reviews/summary?property_id=1",
    );
  });

  it("listReviews — builds URL with query params and unwraps page envelope", async () => {
    const page = {
      data: [
        {
          id: 1,
          property_id: 1,
          ta_hotel_id: 93618,
          post_date: "2012-05-14",
          stay_year: 2012,
          overall: 4.0,
          cleanliness: 4.0,
          value: 4.0,
          location: 5.0,
          rooms: 4.0,
          sleep_quality: 4.0,
          title: "Lovely stay",
          body: "Great!",
          lang: "__label__en",
        },
      ],
      meta: { page: 1, page_size: 200, total: 762, total_pages: 4 },
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(loginBody))
      .mockResolvedValueOnce(jsonResponse(page));
    vi.stubGlobal("fetch", fetchMock);
    const { login, listReviews } = await freshClient();

    await login("manager@buby.travel", "demo");
    const result = await listReviews({ property_id: 1, page: 1, page_size: 200 });

    expect(result.meta.total).toBe(762);
    expect(result.data[0].post_date).toBe("2012-05-14");
    expect(fetchMock.mock.calls[1][0]).toBe(
      "http://localhost:8000/api/reviews?property_id=1&page=1&page_size=200",
    );
  });

  it("listBookings — sends is_canceled and market_segment as query params", async () => {
    const page = {
      data: [
        {
          id: 1,
          property_id: 1,
          arrival_date: "2015-07-01",
          nights: 4,
          adr: 104.5,
          is_canceled: false,
          adults: 2,
          children: 0,
          babies: 0,
          country: "PRT",
          customer_type: "Transient",
          market_segment: "Direct",
          distribution_channel: "Direct",
          deposit_type: "No Deposit",
          lead_time: 74,
        },
      ],
      meta: { page: 1, page_size: 50, total: 87396, total_pages: 1748 },
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(loginBody))
      .mockResolvedValueOnce(jsonResponse(page));
    vi.stubGlobal("fetch", fetchMock);
    const { login, listBookings } = await freshClient();

    await login("manager@buby.travel", "demo");
    const result = await listBookings({
      property_id: 1,
      is_canceled: false,
      market_segment: "Direct",
      page: 1,
      page_size: 50,
    });

    expect(result.meta.total).toBe(87396);
    // is_canceled=false must appear; market_segment must be URL-encoded
    const url: string = fetchMock.mock.calls[1][0];
    expect(url).toContain("is_canceled=false");
    expect(url).toContain("market_segment=Direct");
    expect(url).toContain("property_id=1");
  });

  it("listGuestRequests — sends status filter and unwraps page envelope", async () => {
    const page = {
      data: [
        {
          id: 1,
          property_id: 1,
          received_at: "2017-08-12T09:24:00Z",
          body: "Hello, do you have a room?",
          category: "availability",
          draft_reply: "Dear guest…",
          status: "draft",
        },
      ],
      meta: { page: 1, page_size: 50, total: 800, total_pages: 16 },
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(loginBody))
      .mockResolvedValueOnce(jsonResponse(page));
    vi.stubGlobal("fetch", fetchMock);
    const { login, listGuestRequests } = await freshClient();

    await login("manager@buby.travel", "demo");
    const result = await listGuestRequests({ status: "draft", page: 1 });

    expect(result.meta.total).toBe(800);
    expect(result.data[0].category).toBe("availability");
    const url: string = fetchMock.mock.calls[1][0];
    expect(url).toContain("status=draft");
  });

  it("patchGuestRequest — sends PATCH with body and returns GuestRequest directly (no envelope)", async () => {
    const guestRequest = {
      id: 1,
      property_id: 1,
      received_at: "2017-08-12T09:24:00Z",
      body: "Hello, do you have a room?",
      category: null,
      draft_reply: "Dear guest, yes we have rooms available.",
      status: "draft",
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(loginBody))
      .mockResolvedValueOnce(jsonResponse(guestRequest));
    vi.stubGlobal("fetch", fetchMock);
    const { login, patchGuestRequest } = await freshClient();

    await login("manager@buby.travel", "demo");
    const result = await patchGuestRequest(1, {
      draft_reply: "Dear guest, yes we have rooms available.",
    });

    expect(result).toEqual(guestRequest);
    const [url, init] = fetchMock.mock.calls[1];
    expect(url).toBe("http://localhost:8000/api/guest-requests/1");
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body as string)).toEqual({
      draft_reply: "Dear guest, yes we have rooms available.",
    });
    expect(init.headers.Authorization).toBe("Bearer demo-token");
  });

  it("patchGuestRequest — throws ApiError 403 when role is property_manager", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(loginBody))
      .mockResolvedValueOnce(
        jsonResponse(
          { error: { code: "forbidden", message: "Your role is not allowed to perform this action." } },
          403,
        ),
      );
    vi.stubGlobal("fetch", fetchMock);
    const { login, patchGuestRequest, ApiError } = await freshClient();

    await login("manager@buby.travel", "demo");
    const promise = patchGuestRequest(1, { status: "sent" });
    await expect(promise).rejects.toBeInstanceOf(ApiError);
    await expect(promise).rejects.toMatchObject({
      status: 403,
      code: "forbidden",
    });
  });
});