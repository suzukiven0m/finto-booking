import { useEffect, useState } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ApiError, getReviewSummary, listReviews } from "../api/client";
import type { Review, ReviewSummary } from "../api/types";

// Monthly trend is computed client-side by fetching all /api/reviews pages
// (page_size 200, up to ~9 requests for both properties). The frozen v1 contract
// has no /api/reviews/monthly endpoint: this is the declared approach.

interface MonthlyPoint {
  month: string;
  count: number;
  avgOverall: number | null;
}

function computeMonthlyTrend(reviews: Review[]): MonthlyPoint[] {
  const buckets = new Map<string, { count: number; sum: number; n: number }>();
  for (const r of reviews) {
    const month = r.post_date.slice(0, 7); // "YYYY-MM"
    if (!buckets.has(month)) buckets.set(month, { count: 0, sum: 0, n: 0 });
    const b = buckets.get(month)!;
    b.count++;
    if (r.overall !== null) {
      b.sum += r.overall;
      b.n++;
    }
  }
  return Array.from(buckets.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, { count, sum, n }]) => ({
      month,
      count,
      avgOverall: n > 0 ? Math.round((sum / n) * 100) / 100 : null,
    }));
}

const DIMENSIONS: Array<{ key: keyof ReviewSummary & string; label: string }> = [
  { key: "cleanliness", label: "Pulizia" },
  { key: "value", label: "Rapporto Q/P" },
  { key: "location", label: "Posizione" },
  { key: "rooms", label: "Camere" },
  { key: "sleep_quality", label: "Qualità del sonno" },
];

export default function Reputazione() {
  const [propertyId, setPropertyId] = useState("");
  const [summary, setSummary] = useState<ReviewSummary | null>(null);
  const [trend, setTrend] = useState<MonthlyPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const pid = propertyId === "" ? null : Number(propertyId);

    setLoading(true);
    setError(null);
    setSummary(null);
    setTrend([]);

    async function fetchAll() {
      const all: Review[] = [];
      let page = 1;
      while (!controller.signal.aborted) {
        const r = await listReviews({ property_id: pid, page, page_size: 200 });
        all.push(...r.data);
        if (page >= r.meta.total_pages) break;
        page++;
      }
      return all;
    }

    Promise.all([getReviewSummary({ property_id: pid }), fetchAll()])
      .then(([sum, reviews]) => {
        if (controller.signal.aborted) return;
        setSummary(sum);
        setTrend(computeMonthlyTrend(reviews));
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          err instanceof ApiError
            ? `${err.message} (${err.code})`
            : "Impossibile raggiungere l'API. Mock attivo (npm run mock)?",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [propertyId]);

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
          Proprietà
          <select
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
            value={propertyId}
            onChange={(e) => setPropertyId(e.target.value)}
          >
            <option value="">Entrambe</option>
            <option value="1">Buby Lago</option>
            <option value="2">Buby Montagna</option>
          </select>
        </label>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <p className="py-16 text-center text-sm text-slate-500">
          Caricamento recensioni (pagine da 200)…
        </p>
      )}

      {!loading && summary && (
        <>
          <section className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Overall medio
              </p>
              <p className="mt-1 text-2xl font-semibold text-slate-900">
                {summary.overall.toFixed(2)}
              </p>
              <p className="mt-1 text-xs text-slate-400">su 5</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Recensioni
              </p>
              <p className="mt-1 text-2xl font-semibold text-slate-900">
                {summary.count.toLocaleString("it-IT")}
              </p>
            </div>
          </section>

          <section className="mb-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <h2 className="mb-4 text-sm font-semibold text-slate-700">
              Dimensioni — media reale del corpus (1-5)
            </h2>
            <div className="space-y-3">
              {DIMENSIONS.map(({ key, label }) => {
                const score = summary[key] as number;
                return (
                  <div key={key}>
                    <div className="mb-1 flex justify-between text-xs">
                      <span className="text-slate-700">{label}</span>
                      <span className="font-medium text-slate-900">{score.toFixed(2)}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                      <div
                        className="h-2 rounded-full bg-sky-500"
                        style={{ width: `${(score / 5) * 100}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {trend.length > 0 && (
            <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="mb-1 text-sm font-semibold text-slate-700">
                Trend mensile —{" "}
                <span className="font-semibold text-orange-600">solo 2012</span>
              </h2>
              <p className="mb-4 text-xs text-slate-500">
                <strong>S4:</strong> le recensioni coprono solo il 2012 (post_date
                2012-01-02…2012-12-19); le prenotazioni coprono il 2015-2017:{" "}
                <strong>nessun overlap temporale</strong>. Il trend non è comparabile con i dati
                di occupazione e ricavo, e non implica causalità.
              </p>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={trend} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="count" tick={{ fontSize: 11 }} allowDecimals={false} />
                    <YAxis
                      yAxisId="avg"
                      orientation="right"
                      domain={[1, 5]}
                      tick={{ fontSize: 11 }}
                    />
                    <Tooltip />
                    <Legend />
                    <Bar
                      yAxisId="count"
                      dataKey="count"
                      name="N. recensioni"
                      fill="#bae6fd"
                    />
                    <Line
                      yAxisId="avg"
                      dataKey="avgOverall"
                      name="Overall medio"
                      stroke="#0ea5e9"
                      strokeWidth={2}
                      dot
                      connectNulls
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
