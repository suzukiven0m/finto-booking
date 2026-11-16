import { useEffect, useState } from "react";
import {
  CartesianGrid,
  ComposedChart,
  Area,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ApiError, getKpiDaily, getKpiSummary, getProperties } from "./api/client";
import type { KpiDailyPoint, KpiSummary, Property } from "./api/types";
import { ROLE_LABELS } from "./session";
import type { Session } from "./session";

const eur = new Intl.NumberFormat("it-IT", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 2,
});
const int = new Intl.NumberFormat("it-IT");
const pct = (value: number) =>
  `${(value * 100).toLocaleString("it-IT", { maximumFractionDigits: 2 })}%`;

// Full dataset range (docs/data-dictionary.md §3 baseline).
const DEFAULT_FROM = "2015-07-01";
const DEFAULT_TO = "2017-08-31";

function KpiCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

export default function App({ session, onLogout }: { session: Session; onLogout: () => void }) {
  const [properties, setProperties] = useState<Property[]>([]);
  const [propertyId, setPropertyId] = useState("");
  const [dateFrom, setDateFrom] = useState(DEFAULT_FROM);
  const [dateTo, setDateTo] = useState(DEFAULT_TO);
  const [summary, setSummary] = useState<KpiSummary | null>(null);
  const [daily, setDaily] = useState<KpiDailyPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    getProperties().then(setProperties).catch(() => {
      // Selector falls back to the two known properties; KPI error state covers outages.
    });
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const params = {
      property_id: propertyId === "" ? null : Number(propertyId),
      date_from: dateFrom,
      date_to: dateTo,
    };
    setLoading(true);
    setError(null);
    Promise.all([
      getKpiSummary(params),
      getKpiDaily({ ...params, page_size: 200 }),
    ])
      .then(([summaryResult, dailyResult]) => {
        if (controller.signal.aborted) return;
        setSummary(summaryResult);
        setDaily(dailyResult.data);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          err instanceof ApiError
            ? `${err.message} (${err.code})`
            : "Could not reach the API. Is the mock running (npm run mock)?",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [propertyId, dateFrom, dateTo, reload]);

  const selectorOptions = properties.length
    ? properties
    : ([
        { id: 1, name: "Buby Lago" },
        { id: 2, name: "Buby Montagna" },
      ] as Property[]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-4 px-4 py-5">
          <div>
            <h1 className="text-xl font-semibold">Buby Travel — Dashboard</h1>
            <p className="text-sm text-slate-500">SAL 1 demo · KPIs from the pinned contract v1</p>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
              Property
              <select
                className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
                value={propertyId}
                onChange={(event) => setPropertyId(event.target.value)}
              >
                <option value="">Both</option>
                {selectorOptions.map((property) => (
                  <option key={property.id} value={property.id}>
                    {property.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
              From
              <input
                type="date"
                className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                value={dateFrom}
                onChange={(event) => setDateFrom(event.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
              To
              <input
                type="date"
                className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                value={dateTo}
                onChange={(event) => setDateTo(event.target.value)}
              />
            </label>
            {/* chi e' entrato + logout */}
            <div className="flex items-center gap-3 text-sm">
              <span className="text-slate-500">
                {session.email} · {ROLE_LABELS[session.role] ?? session.role}
              </span>
              <button
                type="button"
                onClick={onLogout}
                className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium hover:bg-slate-100"
              >
                Log out
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {error && (
          <div className="mb-6 flex items-center justify-between gap-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <span>{error}</span>
            <button
              type="button"
              className="rounded-md border border-red-300 px-3 py-1 font-medium hover:bg-red-100"
              onClick={() => setReload((n) => n + 1)}
            >
              Retry
            </button>
          </div>
        )}

        {loading && (
          <p className="py-16 text-center text-sm text-slate-500">Loading KPIs…</p>
        )}

        {!loading && summary && (
          <>
            <section className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
              <KpiCard label="Revenue" value={eur.format(summary.revenue)} />
              <KpiCard label="Room nights" value={int.format(summary.room_nights)} />
              <KpiCard label="ADR" value={eur.format(summary.adr)} />
              <KpiCard label="Cancellation rate" value={pct(summary.cancellation_rate)} />
              <KpiCard
                label="Occupancy (avg)"
                value={pct(summary.occupancy_avg)}
                hint="assumed capacity"
              />
              <KpiCard label="RevPAR" value={eur.format(summary.revpar)} hint="assumed capacity" />
            </section>

            <section className="mt-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="mb-4 text-sm font-semibold text-slate-700">
                Daily revenue & occupancy
              </h2>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={daily} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis
                      yAxisId="revenue"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value: number) => `€${int.format(value)}`}
                    />
                    <YAxis
                      yAxisId="occupancy"
                      orientation="right"
                      domain={[0, 1]}
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value: number) => pct(value)}
                    />
                    <Tooltip
                      formatter={(value: number | string, name: string) =>
                        name === "Revenue" ? eur.format(Number(value)) : pct(Number(value))
                      }
                    />
                    <Legend />
                    <Area
                      yAxisId="revenue"
                      dataKey="revenue"
                      name="Revenue"
                      stroke="#0ea5e9"
                      fill="#e0f2fe"
                      connectNulls
                    />
                    <Line
                      yAxisId="occupancy"
                      dataKey="occupancy"
                      name="Occupancy"
                      stroke="#f59e0b"
                      dot={false}
                      connectNulls
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </section>
          </>
        )}
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-8 text-xs leading-relaxed text-slate-500">
        <p>
          Occupancy & RevPAR use <strong>assumed capacity</strong> (Buby Lago 190 rooms, Buby
          Montagna 230 rooms), not measured. The reviews↔bookings link is{" "}
          <strong>asserted</strong> at property level, not factual; reputation KPIs come only from
          reviews. Guest-request emails are <strong>synthetic</strong>; the properties are fictional
          (1:1 map of the CSV's two hotel types).
        </p>
      </footer>
    </div>
  );
}