import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ApiError, getReviewSummary, listReviews } from "../api/client";
import type { Review, ReviewSummary } from "../api/types";
import { IconAlert, IconLake, IconMountain, IconSearch, IconSparkles } from "../components/Icons";
import { EXTRACTIVE_SUMMARIES_2012, NLP_CORPUS_INSIGHTS } from "../data/corpusInsights";

interface MonthlyPoint {
  month: string;
  count: number;
  avgOverall: number | null;
}

function computeMonthlyTrend(reviews: Review[]): MonthlyPoint[] {
  const buckets = new Map<string, { count: number; sum: number; n: number }>();
  for (const r of reviews) {
    const month = r.post_date.slice(0, 7);
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

export default function Reputazione({
  propertyId,
  onChangePropertyId,
}: {
  propertyId: string;
  onChangePropertyId: (id: string) => void;
}) {
  const [summary, setSummary] = useState<ReviewSummary | null>(null);
  const [lagoSummary, setLagoSummary] = useState<ReviewSummary | null>(null);
  const [montagnaSummary, setMontagnaSummary] = useState<ReviewSummary | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Explorer filters
  const [searchText, setSearchText] = useState("");
  const [starFilter, setStarFilter] = useState<string>("");
  const [sortBy, setSortBy] = useState<"newest" | "highest" | "lowest">("newest");
  const [selectedMonth, setSelectedMonth] = useState<string>("2012-09");

  useEffect(() => {
    const controller = new AbortController();
    const pid = propertyId === "" ? null : Number(propertyId);

    setLoading(true);
    setError(null);

    async function fetchAll() {
      const byId = new Map<number, Review>();
      let page = 1;
      while (!controller.signal.aborted) {
        const r = await listReviews({ property_id: pid, page, page_size: 200 });
        const before = byId.size;
        for (const rev of r.data) {
          if (!byId.has(rev.id)) byId.set(rev.id, rev);
        }
        // Stop early if the server returns no new IDs (e.g. static Prism mock) or last page reached
        if (page >= r.meta.total_pages || byId.size === before) break;
        page++;
      }
      return Array.from(byId.values());
    }

    Promise.all([
      getReviewSummary({ property_id: pid }),
      getReviewSummary({ property_id: 1 }),
      getReviewSummary({ property_id: 2 }),
      fetchAll(),
    ])
      .then(([sum, s1, s2, allReviews]) => {
        if (controller.signal.aborted) return;
        setSummary(sum);
        setLagoSummary(s1);
        setMontagnaSummary(s2);
        setReviews(allReviews);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          err instanceof ApiError
            ? `${err.message} (${err.code})`
            : "Impossibile raggiungere l'API. Verifica backend o mock.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [propertyId]);

  const trend = useMemo(() => computeMonthlyTrend(reviews), [reviews]);

  const radarData = useMemo(() => {
    if (!lagoSummary || !montagnaSummary) return [];
    return DIMENSIONS.map((d) => ({
      dimension: d.label,
      lago: lagoSummary[d.key] as number,
      montagna: montagnaSummary[d.key] as number,
    }));
  }, [lagoSummary, montagnaSummary]);

  const filteredReviews = useMemo(() => {
    const q = searchText.trim().toLowerCase();
    const list = reviews.filter((r) => {
      if (starFilter === "5" && (r.overall ?? 0) < 4.5) return false;
      if (starFilter === "4" && ((r.overall ?? 0) < 3.5 || (r.overall ?? 0) >= 4.5)) return false;
      if (starFilter === "low" && (r.overall ?? 5) > 3) return false;
      if (!q) return true;
      return (
        (r.title ?? "").toLowerCase().includes(q) ||
        (r.body ?? "").toLowerCase().includes(q)
      );
    });

    const sorted = [...list];
    if (sortBy === "highest") {
      sorted.sort((a, b) => (b.overall ?? 0) - (a.overall ?? 0));
    } else if (sortBy === "lowest") {
      sorted.sort((a, b) => (a.overall ?? 5) - (b.overall ?? 5));
    } else {
      sorted.sort((a, b) => b.post_date.localeCompare(a.post_date));
    }
    return sorted;
  }, [reviews, searchText, starFilter, sortBy]);

  const activeExtractive = useMemo(() => {
    const pidFilter = propertyId === "2" ? 2 : 1;
    return (
      EXTRACTIVE_SUMMARIES_2012.find(
        (s) => s.property_id === pidFilter && s.month === selectedMonth,
      ) ?? EXTRACTIVE_SUMMARIES_2012.find((s) => s.property_id === pidFilter)
    );
  }, [propertyId, selectedMonth]);

  const sentimentDist =
    propertyId === "1"
      ? NLP_CORPUS_INSIGHTS.sentimentCounts.lago
      : propertyId === "2"
        ? NLP_CORPUS_INSIGHTS.sentimentCounts.montagna
        : NLP_CORPUS_INSIGHTS.sentimentCounts.pooled;

  const sentTotal = sentimentDist.positive + sentimentDist.neutral + sentimentDist.negative;

  return (
    <div className="animate-enter space-y-6">
      {/* Top property bar + S4 Warning */}
      <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-xs">
        <div className="flex flex-wrap items-center gap-1.5 rounded-xl bg-slate-100 p-1">
          {[
            { id: "", label: "Entrambe (1.638 rec.)", icon: null },
            { id: "1", label: "Buby Lago (762)", icon: <IconLake size={14} /> },
            { id: "2", label: "Buby Montagna (876)", icon: <IconMountain size={14} /> },
          ].map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => onChangePropertyId(opt.id)}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                propertyId === opt.id
                  ? opt.id === "1"
                    ? "bg-teal-600 text-white"
                    : opt.id === "2"
                      ? "bg-amber-600 text-white"
                      : "bg-slate-900 text-white"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {opt.icon}
              {opt.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-orange-200 bg-orange-50 px-3 py-1.5 text-xs text-orange-900">
          <IconAlert size={15} className="shrink-0 text-orange-600" />
          <span>
            <strong>S4 (Zero Overlap):</strong> corpus solo <strong>2012</strong> in inglese; legame con prenotazioni 2015–17 solo asserito.
          </span>
        </div>
      </section>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="rounded-2xl border border-slate-200 bg-white py-16 text-center text-sm text-slate-500">
          Caricamento recensioni TripAdvisor dal database…
        </div>
      )}

      {!loading && summary && (
        <>
          {/* Headline + Radar Comparison */}
          <section className="grid gap-6 lg:grid-cols-12">
            {/* Summary + 5 dimensions */}
            <div className="space-y-4 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs lg:col-span-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Voto medio reale ospiti
                  </p>
                  <div className="mt-1 flex items-baseline gap-2">
                    <span className="font-mono text-4xl font-extrabold text-slate-900 tabular-nums">
                      {summary.overall.toFixed(2)}
                    </span>
                    <span className="text-sm font-medium text-slate-400">/ 5.00</span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Volume corpus
                  </p>
                  <p className="mt-1 font-mono text-2xl font-bold text-slate-900 tabular-nums">
                    {summary.count.toLocaleString("it-IT")}
                  </p>
                </div>
              </div>

              <div className="space-y-3 pt-2">
                {DIMENSIONS.map(({ key, label }) => {
                  const score = summary[key] as number;
                  return (
                    <div key={key}>
                      <div className="mb-1 flex justify-between text-xs">
                        <span className="font-medium text-slate-700">{label}</span>
                        <span className="font-mono font-semibold text-slate-900 tabular-nums">
                          {score.toFixed(2)} / 5
                        </span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-teal-500 to-sky-500 transition-all duration-500"
                          style={{ width: `${(score / 5) * 100}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 5-Dimension Radar Lago vs Montagna */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs lg:col-span-6">
              <div className="mb-2 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">
                    Profilo Reputazionale: Lago vs Montagna
                  </h2>
                  <p className="text-xs text-slate-500">
                    Confronto diretto sulle 5 dimensioni TripAdvisor (scala 1–5).
                  </p>
                </div>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#e2e8f0" />
                    <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11, fill: "#334155" }} />
                    <PolarRadiusAxis domain={[2.5, 5]} tick={{ fontSize: 10 }} />
                    <Radar
                      name="Buby Lago"
                      dataKey="lago"
                      stroke="#0d9488"
                      fill="#0d9488"
                      fillOpacity={0.25}
                      strokeWidth={2}
                    />
                    <Radar
                      name="Buby Montagna"
                      dataKey="montagna"
                      stroke="#d97706"
                      fill="#f59e0b"
                      fillOpacity={0.2}
                      strokeWidth={2}
                    />
                    <Legend />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          {/* NLP Topic & Sentiment Panel (Precomputed DA artifact) */}
          <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="flex items-center gap-2 text-sm font-bold text-slate-900">
                  <IconSparkles size={16} className="text-teal-600" />
                  Fattori di Soddisfazione & Topic NLP (Analisi DA Pre-calcolata)
                </h2>
                <p className="mt-0.5 text-xs text-slate-500">
                  Modelli zero-shot <code className="font-mono">xlm-roberta</code> (sentiment) e{" "}
                  <code className="font-mono">bart-large-mnli</code> (topic). Statistiche descrittive su etichette deboli 2012, non output live dell'API.
                </p>
              </div>

              {/* Sentiment pill bar */}
              <div className="flex items-center gap-2 text-xs">
                <span className="rounded-full bg-emerald-50 px-2.5 py-1 font-semibold text-emerald-700">
                  Pos: {Math.round((sentimentDist.positive / sentTotal) * 100)}%
                </span>
                <span className="rounded-full bg-slate-100 px-2.5 py-1 font-semibold text-slate-700">
                  Neu: {Math.round((sentimentDist.neutral / sentTotal) * 100)}%
                </span>
                <span className="rounded-full bg-rose-50 px-2.5 py-1 font-semibold text-rose-700">
                  Neg: {Math.round((sentimentDist.negative / sentTotal) * 100)}%
                </span>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {NLP_CORPUS_INSIGHTS.topics.map((t) => {
                const prev =
                  propertyId === "1"
                    ? t.prevalenceLago
                    : propertyId === "2"
                      ? t.prevalenceMontagna
                      : t.prevalencePooled;
                const isRisk = (t.deltaPooled ?? 0) < 0;
                return (
                  <div
                    key={t.topic}
                    className={`rounded-xl border p-3.5 ${
                      isRisk ? "border-rose-200 bg-rose-50/40" : "border-slate-200/80 bg-slate-50/50"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-bold text-slate-900">{t.labelIt}</span>
                      <span className="font-mono text-xs font-semibold text-slate-700">
                        {Math.round(prev * 100)}% menz.
                      </span>
                    </div>
                    {t.deltaPooled !== null && (
                      <p
                        className={`mt-1 text-[11px] font-semibold ${
                          isRisk ? "text-rose-700" : "text-teal-700"
                        }`}
                      >
                        Delta {t.mappedDimension}: {t.deltaPooled > 0 ? "+" : ""}
                        {t.deltaPooled.toFixed(2)} punti
                      </p>
                    )}
                    <p className="mt-1 text-[11px] leading-relaxed text-slate-600">{t.note}</p>
                  </div>
                );
              })}
            </div>
          </section>

          {/* 2012 Monthly Trend + Extractive Highlights */}
          {trend.length > 0 && (
            <section className="grid gap-6 lg:grid-cols-12">
              <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs lg:col-span-7">
                <div className="mb-3 flex items-center justify-between">
                  <div>
                    <h2 className="text-sm font-bold text-slate-900">
                      Trend mensile — <span className="text-orange-600">solo 2012</span>
                    </h2>
                    <p className="text-xs text-slate-500">
                      Non comparabile con i dati di occupazione/ricavo 2015–2017.
                    </p>
                  </div>
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={trend} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                      <YAxis yAxisId="count" tick={{ fontSize: 11 }} allowDecimals={false} />
                      <YAxis yAxisId="avg" orientation="right" domain={[1, 5]} tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Legend />
                      <Bar yAxisId="count" dataKey="count" name="N. recensioni" fill="#cbd5e1" radius={[4, 4, 0, 0]} />
                      <Line
                        yAxisId="avg"
                        dataKey="avgOverall"
                        name="Overall medio"
                        stroke="#0d9488"
                        strokeWidth={2.5}
                        dot
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Extractive 2012 highlights */}
              <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs lg:col-span-5">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div>
                    <h2 className="text-sm font-bold text-slate-900">
                      Sintesi Estrattive 2012
                    </h2>
                    <p className="text-xs text-slate-500">
                      Frasi reali tracciabili dal corpus TripAdvisor (lead-bias, senza LLM).
                    </p>
                  </div>
                  <select
                    aria-label="Mese sintesi 2012"
                    value={selectedMonth}
                    onChange={(e) => setSelectedMonth(e.target.value)}
                    className="shrink-0 whitespace-nowrap rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium"
                  >
                    {["2012-01", "2012-04", "2012-06", "2012-08", "2012-09", "2012-10", "2012-12"].map(
                      (m) => (
                        <option key={m} value={m}>
                          {m}
                        </option>
                      ),
                    )}
                  </select>
                </div>

                {activeExtractive ? (
                  <div className="space-y-2.5">
                    <p className="text-xs text-slate-500">
                      {activeExtractive.property_id === 1 ? "Buby Lago" : "Buby Montagna"} ·{" "}
                      {activeExtractive.n_reviews} recensioni nel mese {activeExtractive.month}
                    </p>
                    {activeExtractive.sentences.map((s, i) => (
                      <blockquote
                        key={i}
                        className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-800"
                      >
                        “{s.text}”
                        <footer className="mt-1.5 flex items-center justify-between text-[10px] text-slate-400">
                          <span>review_id #{s.review_id} · {s.post_date}</span>
                          <span className="font-mono">score {s.score.toFixed(3)}</span>
                        </footer>
                      </blockquote>
                    ))}
                  </div>
                ) : null}
              </div>
            </section>
          )}

          {/* Review Explorer */}
          <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-slate-900">
                  Review Explorer ({filteredReviews.length} su {reviews.length})
                </h2>
                <p className="text-xs text-slate-500">
                  Cerca parole chiave (es. <em>noise, breakfast, staff, clean</em>) tra le recensioni del corpus.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5">
                  <IconSearch size={14} className="text-slate-400" />
                  <input
                    type="text"
                    placeholder="Cerca testo o titolo…"
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    className="w-44 bg-transparent text-xs text-slate-800 outline-none placeholder:text-slate-400"
                  />
                </div>

                <select
                  aria-label="Filtra per stelle"
                  value={starFilter}
                  onChange={(e) => setStarFilter(e.target.value)}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700"
                >
                  <option value="">Tutti i voti</option>
                  <option value="5">Eccellenti (≥ 4.5★)</option>
                  <option value="4">Buone (3.5–4.4★)</option>
                  <option value="low">Critiche (≤ 3★)</option>
                </select>

                <select
                  aria-label="Ordina recensioni"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700"
                >
                  <option value="newest">Più recenti (2012)</option>
                  <option value="highest">Voto più alto</option>
                  <option value="lowest">Voto più basso</option>
                </select>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              {filteredReviews.slice(0, 12).map((r) => (
                <article
                  key={r.id}
                  className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-4 transition hover:bg-white hover:shadow-xs"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="text-xs font-bold text-slate-900">
                        {r.title || `Recensione #${r.id}`}
                      </h3>
                      <p className="text-[11px] text-slate-400">
                        {r.property_id === 1 ? "Buby Lago" : "Buby Montagna"} · {r.post_date}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-2 py-0.5 font-mono text-xs font-bold ${
                        (r.overall ?? 0) >= 4
                          ? "bg-teal-100 text-teal-800"
                          : (r.overall ?? 0) >= 3
                            ? "bg-amber-100 text-amber-800"
                            : "bg-rose-100 text-rose-800"
                      }`}
                    >
                      {r.overall?.toFixed(1) ?? "—"} ★
                    </span>
                  </div>
                  {r.body && (
                    <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-slate-600">
                      {r.body}
                    </p>
                  )}
                  <div className="mt-3 flex flex-wrap gap-1.5 text-[10px] text-slate-500">
                    {r.cleanliness !== null && (
                      <span className="rounded bg-white px-1.5 py-0.5 ring-1 ring-slate-200">
                        Pulizia {r.cleanliness}
                      </span>
                    )}
                    {r.value !== null && (
                      <span className="rounded bg-white px-1.5 py-0.5 ring-1 ring-slate-200">
                        Q/P {r.value}
                      </span>
                    )}
                    {r.sleep_quality !== null && (
                      <span className="rounded bg-white px-1.5 py-0.5 ring-1 ring-slate-200">
                        Sonno {r.sleep_quality}
                      </span>
                    )}
                  </div>
                </article>
              ))}
            </div>
            {filteredReviews.length > 12 && (
              <p className="mt-3 text-center text-xs text-slate-400">
                Visualizzate le prime 12 recensioni su {filteredReviews.length} corrispondenti. Usa la ricerca per affinare.
              </p>
            )}
          </section>
        </>
      )}
    </div>
  );
}
