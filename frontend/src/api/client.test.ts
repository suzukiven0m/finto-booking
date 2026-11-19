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
    expect(loginUrl).toBe("http://localhost:4010/api/auth/login");
    expect(loginInit.method).toBe("POST");
    const [summaryUrl, summaryInit] = fetchMock.mock.calls[1];
    // null property_id (both properties) is omitted from the query string
    expect(summaryUrl).toBe(
      "http://localhost:4010/api/kpis/summary?date_from=2015-07-01&date_to=2017-08-31",
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
      "http://localhost:4010/api/kpis/daily?property_id=1&page_size=200",
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