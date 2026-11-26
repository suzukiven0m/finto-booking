import { useEffect, useMemo, useState } from "react";
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ApiError,
  getKpiChannels,
  getKpiDaily,
  getKpiSeasonality,
  getKpiSummary,
} from "../api/client";
import type {
  ChannelMixItem,
  KpiDailyPoint,
  KpiSummary,
  Property,
  SeasonalityPoint,
} from "../api/types";
import {
  IconAlert,
  IconCalendar,
  IconCompare,
  IconLake,
  IconMountain,
  IconSliders,
  IconTrendingUp,
} from "../components/Icons";
import { LEAD_TIME_RISK_BUCKETS } from "../data/corpusInsights";

const eur = new Intl.NumberFormat("it-IT", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 2,
});
const eurCompact = new Intl.NumberFormat("it-IT", {
  style: "currency",
  currency: "EUR",
  notation: "compact",
  maximumFractionDigits: 1,
});
const int = new Intl.NumberFormat("it-IT");
const pct = (value: number) =>
  `${(value * 100).toLocaleString("it-IT", { maximumFractionDigits: 2 })}%`;

const MONTH_NAMES = [
  "Gen",
  "Feb",
  "Mar",
  "Apr",
  "Mag",
  "Giu",
  "Lug",
  "Ago",
  "Set",
  "Ott",
  "Nov",
  "Dic",
];

const CHANNEL_COLORS = [
  "#0d9488",
  "#0284c7",
  "#f59e0b",
  "#6366f1",
  "#ec4899",
  "#64748b",
  "#10b981",
  "#94a3b8",
];

export const DEFAULT_FROM = "2015-07-01";
export const DEFAULT_TO = "2017-08-31";

const DATE_PRESETS = [
  { label: "Tutto (2015–17)", from: "2015-07-01", to: "2017-08-31" },
  { label: "Anno 2016", from: "2016-01-01", to: "2016-12-31" },
  { label: "Estate '16 (Giu–Ago)", from: "2016-06-01", to: "2016-08-31" },
  { label: "Inverno '16–17", from: "2016-11-01", to: "2017-02-28" },
];

type ChartMode = "revenue_occ" | "adr_revpar" | "room_nights";
type Granularity = "daily" | "monthly";

function KpiCard({
  label,
  value,
  sub,
  badge,
  progress,
  tone = "slate",
}: {
  label: string;
  value: string;
  sub?: string;
  badge?: string;
  progress?: number;
  tone?: "slate" | "teal" | "amber" | "rose";
}) {
  const barColors = {
    slate: "bg-slate-800",
    teal: "bg-teal-600",
    amber: "bg-amber-500",
    rose: "bg-rose-500",
  };
  return (
    <div className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-4 shadow-xs transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex flex-wrap items-center justify-between gap-1.5">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          {label}
        </p>
        {badge && (
          <span className="shrink-0 whitespace-nowrap rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600">
            {badge}
          </span>
        )}
      </div>
      <p className="mt-2 font-mono text-xl font-bold tracking-tight text-slate-900 tabular-nums sm:text-2xl">
        {value}
      </p>
      {progress !== undefined && (
        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className={`h-full rounded-full transition-all duration-500 ${barColors[tone]}`}
            style={{ width: `${Math.min(100, Math.max(0, progress * 100))}%` }}
          />
        </div>
      )}
      {sub && <p className="mt-2 text-[11px] text-slate-400">{sub}</p>}
    </div>
  );
}

export default function Dashboard({
  properties,
  propertyId,
  onChangePropertyId,
}: {
  properties: Property[];
  propertyId: string;
  onChangePropertyId: (id: string) => void;
}) {
  const [dateFrom, setDateFrom] = useState(DEFAULT_FROM);
  const [dateTo, setDateTo] = useState(DEFAULT_TO);
  const [summary, setSummary] = useState<KpiSummary | null>(null);
  const [daily, setDaily] = useState<KpiDailyPoint[]>([]);
  const [dailyTotalDays, setDailyTotalDays] = useState(0);
  const [channels, setChannels] = useState<ChannelMixItem[]>([]);
  const [seasonality, setSeasonality] = useState<SeasonalityPoint[]>([]);

  // Optional live side-by-side comparison (Lago vs Montagna)
  const [showCompare, setShowCompare] = useState(true);
  const [compareData, setCompareData] = useState<{ lago: KpiSummary; montagna: KpiSummary } | null>(
    null,
  );

  const [chartMode, setChartMode] = useState<ChartMode>("revenue_occ");
  const [granularity, setGranularity] = useState<Granularity>("monthly");
  const [loading, setLoading] = useState(true);
  const [loadingMoreDaily, setLoadingMoreDaily] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  // What-if simulator state (illustrative arithmetic only)
  const [adrDelta, setAdrDelta] = useState(0);
  const [cancelDeltaPp, setCancelDeltaPp] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const pid = propertyId === "" ? null : Number(propertyId);
    const params = { property_id: pid, date_from: dateFrom, date_to: dateTo };

    setLoading(true);
    setError(null);
    setLoadingMoreDaily(false);

    async function load() {
      const [summaryRes, dailyPage1, channelsRes, seasonalityRes] = await Promise.all([
        getKpiSummary(params),
        getKpiDaily({ ...params, page: 1, page_size: 200 }),
        getKpiChannels(params),
        getKpiSeasonality({ property_id: pid }),
      ]);

      if (controller.signal.aborted) return;
      setSummary(summaryRes);
      setDaily(dailyPage1.data);
      setDailyTotalDays(dailyPage1.meta.total);
      setChannels(channelsRes);
      setSeasonality(seasonalityRes);
      setLoading(false);

      // Progressively load remaining daily pages (up to 806 days) for complete chart view
      if (dailyPage1.meta.total_pages > 1) {
        setLoadingMoreDaily(true);
        const restPages: Promise<Awaited<ReturnType<typeof getKpiDaily>>>[] = [];
        for (let p = 2; p <= dailyPage1.meta.total_pages; p++) {
          restPages.push(getKpiDaily({ ...params, page: p, page_size: 200 }));
        }
        const results = await Promise.all(restPages);
        if (!controller.signal.aborted) {
          const byDate = new Map<string, KpiDailyPoint>();
          for (const pt of [...dailyPage1.data, ...results.flatMap((r) => r.data)]) {
            if (!byDate.has(pt.date)) byDate.set(pt.date, pt);
          }
          const merged = Array.from(byDate.values());
          setDaily(merged);
          // When a mock server repeats only a single month, switch to daily view so the curve renders clearly
          const distinctMonths = new Set(merged.map((d) => d.date.slice(0, 7)));
          if (distinctMonths.size <= 1 && merged.length > 1) {
            setGranularity("daily");
          }
          setLoadingMoreDaily(false);
        }
      }
    }

    load().catch((err: unknown) => {
      if (controller.signal.aborted) return;
      setLoading(false);
      setLoadingMoreDaily(false);
      setError(
        err instanceof ApiError
          ? `${err.message} (${err.code})`
          : "Impossibile raggiungere l'API. Verifica backend (:8000) o mock (:4010).",
      );
    });

    return () => controller.abort();
  }, [propertyId, dateFrom, dateTo, reload]);

  // Fetch side-by-side comparison whenever requested
  useEffect(() => {
    if (!showCompare) return;
    let active = true;
    Promise.all([
      getKpiSummary({ property_id: 1, date_from: dateFrom, date_to: dateTo }),
      getKpiSummary({ property_id: 2, date_from: dateFrom, date_to: dateTo }),
    ])
      .then(([lago, montagna]) => {
        if (active) setCompareData({ lago, montagna });
      })
      .catch(() => {
        // Non-blocking: main error banner handles API outage
      });
    return () => {
      active = false;
    };
  }, [showCompare, dateFrom, dateTo, reload]);

  // Aggregate daily stay-days by YYYY-MM when granularity === "monthly"
  const chartSeries = useMemo(() => {
    if (granularity === "daily") {
      return daily.map((d) => ({
        label: d.date,
        revenue: d.revenue,
        occupancy: d.occupancy,
        adr: d.adr ?? 0,
        revpar: d.revenue_per_available_room,
        room_nights: d.room_nights,
      }));
    }
    const buckets = new Map<
      string,
      { days: number; nights: number; rev: number; occSum: number; revparSum: number }
    >();
    for (const d of daily) {
      const m = d.date.slice(0, 7);
      const b = buckets.get(m) ?? { days: 0, nights: 0, rev: 0, occSum: 0, revparSum: 0 };
      b.days++;
      b.nights += d.room_nights;
      b.rev += d.revenue;
      b.occSum += d.occupancy;
      b.revparSum += d.revenue_per_available_room;
      buckets.set(m, b);
    }
    return Array.from(buckets.entries()).map(([month, b]) => ({
      label: month,
      revenue: Math.round(b.rev),
      occupancy: Math.round((b.occSum / b.days) * 10000) / 10000,
      adr: b.nights > 0 ? Math.round((b.rev / b.nights) * 100) / 100 : 0,
      revpar: Math.round((b.revparSum / b.days) * 100) / 100,
      room_nights: b.nights,
    }));
  }, [daily, granularity]);

  const seasonalityLabeled = useMemo(
    () =>
      seasonality.map((s) => ({
        ...s,
        monthLabel: MONTH_NAMES[s.month - 1] ?? String(s.month),
      })),
    [seasonality],
  );

  // What-if simulator arithmetic
  const simulated = useMemo(() => {
    if (!summary) return null;
    const baseAdr = summary.adr;
    const simAdr = Math.max(20, baseAdr + adrDelta);
    const currentCancel = summary.cancellation_rate;
    const simCancel = Math.min(0.8, Math.max(0, currentCancel + cancelDeltaPp / 100));
    // Relative retention multiplier based on (1 - simCancel) / (1 - currentCancel)
    const retentionFactor =
      1 - currentCancel > 0 ? (1 - simCancel) / (1 - currentCancel) : 1;
    const simNights = Math.round(summary.room_nights * retentionFactor);
    const simRevenue = simAdr * simNights;
    const deltaRevenue = simRevenue - summary.revenue;
    const deltaPct = summary.revenue > 0 ? deltaRevenue / summary.revenue : 0;
    const impliedDays =
      summary.revpar > 0 && summary.revenue > 0
        ? summary.revenue / summary.revpar / (propertyId === "1" ? 190 : propertyId === "2" ? 230 : 420)
        : 1;
    const rooms = propertyId === "1" ? 190 : propertyId === "2" ? 230 : 420;
    const simRevpar = rooms * impliedDays > 0 ? simRevenue / (rooms * impliedDays) : summary.revpar;

    return {
      simAdr,
      simCancel,
      simNights,
      simRevenue,
      deltaRevenue,
      deltaPct,
      simRevpar,
    };
  }, [summary, adrDelta, cancelDeltaPp, propertyId]);

  const selectorOptions = properties.length
    ? properties
    : ([
        { id: 1, name: "Buby Lago", room_count: 190 },
        { id: 2, name: "Buby Montagna", room_count: 230 },
      ] as Property[]);

  return (
    <div className="animate-enter space-y-6">
      {/* Control Ribbon */}
      <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Property pills */}
          <div className="flex flex-wrap items-center gap-1.5 rounded-xl bg-slate-100 p-1">
            <button
              type="button"
              onClick={() => onChangePropertyId("")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                propertyId === ""
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Entrambe (420 cam.)
            </button>
            {selectorOptions.map((p) => {
              const active = propertyId === String(p.id);
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => onChangePropertyId(String(p.id))}
                  className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                    active
                      ? p.id === 1
                        ? "bg-teal-600 text-white shadow-xs"
                        : "bg-amber-600 text-white shadow-xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  {p.id === 1 ? <IconLake size={14} /> : <IconMountain size={14} />}
                  {p.name} ({p.room_count})
                </button>
              );
            })}
          </div>

          {/* Date presets + inputs */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="hidden flex-wrap gap-1 xl:flex">
              {DATE_PRESETS.map((preset) => {
                const isSelected = dateFrom === preset.from && dateTo === preset.to;
                return (
                  <button
                    key={preset.label}
                    type="button"
                    onClick={() => {
                      setDateFrom(preset.from);
                      setDateTo(preset.to);
                    }}
                    className={`rounded-lg border px-2.5 py-1.5 text-xs font-medium transition ${
                      isSelected
                        ? "border-teal-600 bg-teal-50 text-teal-800"
                        : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    {preset.label}
                  </button>
                );
              })}
            </div>

            <div className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-2.5 py-1">
              <IconCalendar size={14} className="text-slate-400" />
              <input
                type="date"
                aria-label="Data inizio"
                className="bg-transparent text-xs font-medium text-slate-800 outline-none"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
              <span className="text-slate-300">→</span>
              <input
                type="date"
                aria-label="Data fine"
                className="bg-transparent text-xs font-medium text-slate-800 outline-none"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>

            <button
              type="button"
              onClick={() => setShowCompare((v) => !v)}
              className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-semibold transition ${
                showCompare
                  ? "border-slate-900 bg-slate-900 text-white"
                  : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              <IconCompare size={14} />
              Confronto
            </button>
          </div>
        </div>
      </section>

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <span className="flex items-center gap-2">
            <IconAlert size={16} />
            {error}
          </span>
          <button
            type="button"
            className="rounded-lg border border-red-300 bg-white px-3 py-1 text-xs font-semibold hover:bg-red-100"
            onClick={() => setReload((n) => n + 1)}
          >
            Riprova
          </button>
        </div>
      )}

      {loading && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-2xl border border-slate-200 bg-white" />
          ))}
        </div>
      )}

      {!loading && summary && (
        <>
          {/* 6 KPI cards */}
          <section className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
            <KpiCard
              label="Ricavo realizzato"
              value={eurCompact.format(summary.revenue)}
              sub={eur.format(summary.revenue)}
              badge={`${int.format(summary.valid_bookings)} pren.`}
              tone="teal"
            />
            <KpiCard
              label="Room-nights"
              value={int.format(summary.room_nights)}
              sub="Notti valide nella coorte"
            />
            <KpiCard
              label="ADR medio"
              value={eur.format(summary.adr)}
              sub="Tariffa media giornaliera"
              tone="teal"
            />
            <KpiCard
              label="RevPAR"
              value={eur.format(summary.revpar)}
              badge="cap. assunta"
              sub="Ricavo per camera disponibile"
            />
            <KpiCard
              label="Occupazione media"
              value={pct(summary.occupancy_avg)}
              badge="cap. assunta"
              progress={summary.occupancy_avg}
              tone="teal"
              sub={
                propertyId === "1"
                  ? "Base 190 camere"
                  : propertyId === "2"
                    ? "Base 230 camere"
                    : "Base 420 camere"
              }
            />
            <KpiCard
              label="Cancellazioni"
              value={pct(summary.cancellation_rate)}
              progress={summary.cancellation_rate}
              tone="rose"
              sub="Quota su righe post-dedup"
            />
          </section>

          {/* Side-by-side Property Comparison */}
          {showCompare && compareData && (
            <section className="grid gap-4 md:grid-cols-2">
              {[
                {
                  id: "1",
                  name: "Buby Lago",
                  tag: "Resort Hotel · 190 cam. assunte",
                  data: compareData.lago,
                  accent: "border-teal-200/80 bg-gradient-to-br from-white to-teal-50/40",
                  pill: "bg-teal-100 text-teal-800",
                  icon: <IconLake size={18} className="text-teal-600" />,
                },
                {
                  id: "2",
                  name: "Buby Montagna",
                  tag: "City Hotel · 230 cam. assunte",
                  data: compareData.montagna,
                  accent: "border-amber-200/80 bg-gradient-to-br from-white to-amber-50/40",
                  pill: "bg-amber-100 text-amber-800",
                  icon: <IconMountain size={18} className="text-amber-600" />,
                },
              ].map((prop) => (
                <div
                  key={prop.id}
                  onClick={() => onChangePropertyId(prop.id)}
                  className={`cursor-pointer rounded-2xl border p-4 shadow-xs transition hover:shadow-md ${prop.accent} ${
                    propertyId === prop.id ? "ring-2 ring-slate-900/15" : ""
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white shadow-xs">
                        {prop.icon}
                      </span>
                      <div>
                        <h3 className="text-sm font-bold text-slate-900">{prop.name}</h3>
                        <p className="text-[11px] text-slate-500">{prop.tag}</p>
                      </div>
                    </div>
                    <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${prop.pill}`}>
                      Occ. {pct(prop.data.occupancy_avg)}
                    </span>
                  </div>

                  <div className="mt-4 grid grid-cols-4 gap-2 border-t border-slate-200/60 pt-3 text-xs">
                    <div>
                      <p className="text-[10px] text-slate-400">Ricavo</p>
                      <p className="font-mono font-semibold text-slate-800 tabular-nums">
                        {eurCompact.format(prop.data.revenue)}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-400">ADR</p>
                      <p className="font-mono font-semibold text-slate-800 tabular-nums">
                        {eur.format(prop.data.adr)}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-400">RevPAR</p>
                      <p className="font-mono font-semibold text-slate-800 tabular-nums">
                        {eur.format(prop.data.revpar)}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-400">Cancel.</p>
                      <p className="font-mono font-semibold text-rose-600 tabular-nums">
                        {pct(prop.data.cancellation_rate)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </section>
          )}

          {/* Main Time-Series Chart */}
          <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="flex items-center gap-2 text-sm font-bold text-slate-900">
                  <IconTrendingUp size={16} className="text-teal-600" />
                  Andamento temporale Stay-Days ({daily.length}/{dailyTotalDays || daily.length} giorni)
                  {loadingMoreDaily && (
                    <span className="rounded-full bg-teal-50 px-2 py-0.5 text-[10px] font-medium text-teal-700">
                      Caricamento serie completa…
                    </span>
                  )}
                </h2>
                <p className="mt-0.5 text-xs text-slate-500">
                  Il riepilogo in alto usa la coorte di arrivo; questo grafico conta i giorni effettivi di soggiorno.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <div className="flex rounded-lg bg-slate-100 p-0.5 text-xs">
                  {(
                    [
                      ["monthly", "Mensile"],
                      ["daily", "Giornaliero"],
                    ] as Array<[Granularity, string]>
                  ).map(([g, label]) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setGranularity(g)}
                      className={`rounded-md px-2.5 py-1 font-medium transition ${
                        granularity === g ? "bg-white text-slate-900 shadow-xs" : "text-slate-500"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                <div className="flex rounded-lg bg-slate-100 p-0.5 text-xs">
                  {(
                    [
                      ["revenue_occ", "Ricavo & Occ."],
                      ["adr_revpar", "ADR & RevPAR"],
                      ["room_nights", "Room-Nights"],
                    ] as Array<[ChartMode, string]>
                  ).map(([m, label]) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setChartMode(m)}
                      className={`rounded-md px-2.5 py-1 font-medium transition ${
                        chartMode === m ? "bg-white text-slate-900 shadow-xs" : "text-slate-500"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                {chartMode === "revenue_occ" ? (
                  <ComposedChart data={chartSeries} margin={{ top: 8, right: 12, bottom: 4, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis
                      yAxisId="left"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v: number) => eurCompact.format(v)}
                    />
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      domain={[0, 1]}
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v: number) => pct(v)}
                    />
                    <Tooltip
                      formatter={(val: number | string, name: string) =>
                        name === "Occupazione" ? pct(Number(val)) : eur.format(Number(val))
                      }
                    />
                    <Legend />
                    <Area
                      yAxisId="left"
                      dataKey="revenue"
                      name="Ricavo"
                      stroke="#0d9488"
                      fill="#ccfbf1"
                      strokeWidth={2}
                    />
                    <Line
                      yAxisId="right"
                      dataKey="occupancy"
                      name="Occupazione"
                      stroke="#f59e0b"
                      strokeWidth={2}
                      dot={granularity === "monthly"}
                    />
                  </ComposedChart>
                ) : chartMode === "adr_revpar" ? (
                  <ComposedChart data={chartSeries} margin={{ top: 8, right: 12, bottom: 4, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) => `€${v}`} />
                    <Tooltip formatter={(val: number | string) => eur.format(Number(val))} />
                    <Legend />
                    <Line
                      dataKey="adr"
                      name="ADR (€)"
                      stroke="#0284c7"
                      strokeWidth={2}
                      dot={granularity === "monthly"}
                    />
                    <Area
                      dataKey="revpar"
                      name="RevPAR (€)"
                      stroke="#0d9488"
                      fill="#ccfbf1"
                      strokeWidth={2}
                    />
                  </ComposedChart>
                ) : (
                  <BarChart data={chartSeries} margin={{ top: 8, right: 12, bottom: 4, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(val: number | string) => int.format(Number(val))} />
                    <Legend />
                    <Bar dataKey="room_nights" name="Room-nights" fill="#0f172a" radius={[4, 4, 0, 0]} />
                  </BarChart>
                )}
              </ResponsiveContainer>
            </div>
          </section>

          {/* Seasonality + Channel Mix Grid */}
          <section className="grid gap-6 lg:grid-cols-12">
            {/* Seasonality */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs lg:col-span-7">
              <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">
                    Stagionalità (medie per mese dell'anno)
                  </h2>
                  <p className="text-xs text-slate-500">
                    Medie storiche 1–12 mesi (mai totali grezzi, perché 2015 e 2017 sono anni parziali).
                  </p>
                </div>
                <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-semibold text-slate-600">
                  GET /api/kpis/seasonality
                </span>
              </div>

              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={seasonalityLabeled} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="monthLabel" tick={{ fontSize: 11 }} />
                    <YAxis
                      yAxisId="adr"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v: number) => `€${v}`}
                    />
                    <YAxis
                      yAxisId="occ"
                      orientation="right"
                      domain={[0, 1]}
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v: number) => pct(v)}
                    />
                    <Tooltip
                      formatter={(val: number | string, name: string) =>
                        name === "Occupazione media" ? pct(Number(val)) : eur.format(Number(val))
                      }
                    />
                    <Legend />
                    <Bar
                      yAxisId="adr"
                      dataKey="avg_adr"
                      name="ADR medio (€)"
                      fill="#0d9488"
                      radius={[4, 4, 0, 0]}
                    />
                    <Line
                      yAxisId="occ"
                      dataKey="avg_occupancy"
                      name="Occupazione media"
                      stroke="#f59e0b"
                      strokeWidth={2.5}
                      dot
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Channel Mix */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs lg:col-span-5">
              <div className="mb-3 flex items-start justify-between gap-2">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">
                    Mix Canali di Vendita
                  </h2>
                  <p className="text-xs text-slate-500">
                    Quota prenotazioni valide per <code className="font-mono">market_segment</code> (ID OTA non mappati).
                  </p>
                </div>
                <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-semibold text-slate-600">
                  /channels
                </span>
              </div>

              <div className="space-y-2.5">
                {channels.map((ch, idx) => {
                  const color = CHANNEL_COLORS[idx % CHANNEL_COLORS.length];
                  const revPerBooking = ch.bookings > 0 ? ch.revenue / ch.bookings : 0;
                  return (
                    <div key={ch.market_segment} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-800">{ch.market_segment}</span>
                        <span className="font-mono text-slate-600 tabular-nums">
                          {pct(ch.share)} · {eurCompact.format(ch.revenue)} ({eur.format(revPerBooking)}/pren.)
                        </span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.max(2, ch.share * 100)}%`,
                            backgroundColor: color,
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>

          {/* Bottom Row: What-If Pricing Simulator + Lead-time Risk Intelligence */}
          <section className="grid gap-6 lg:grid-cols-12">
            {/* Interactive What-If Simulator */}
            <div className="rounded-2xl border border-teal-200/80 bg-gradient-to-br from-white to-teal-50/30 p-5 shadow-xs lg:col-span-7">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="flex items-center gap-2 text-sm font-bold text-slate-900">
                    <IconSliders size={16} className="text-teal-600" />
                    Simulatore Decisionale Tariffe & Cancellazioni
                  </h2>
                  <p className="mt-0.5 text-xs text-slate-500">
                    Esplora scenari aritmetici sui KPI della finestra selezionata (nessuna stima di elasticità causale).
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setAdrDelta(0);
                    setCancelDeltaPp(0);
                  }}
                  className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50"
                >
                  Azzera scenario
                </button>
              </div>

              <div className="mt-5 grid gap-5 sm:grid-cols-2">
                <label className="block rounded-xl border border-slate-200 bg-white p-3.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-700">Variazione ADR target</span>
                    <span className="font-mono font-bold text-teal-700">
                      {adrDelta >= 0 ? `+${adrDelta}` : adrDelta} €
                    </span>
                  </div>
                  <input
                    type="range"
                    min={-20}
                    max={30}
                    step={1}
                    value={adrDelta}
                    onChange={(e) => setAdrDelta(Number(e.target.value))}
                    className="mt-3 w-full accent-teal-600"
                  />
                  <div className="mt-1 flex justify-between text-[10px] text-slate-400">
                    <span>-20 €</span>
                    <span>Base: {eur.format(summary.adr)}</span>
                    <span>+30 €</span>
                  </div>
                </label>

                <label className="block rounded-xl border border-slate-200 bg-white p-3.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-700">Riduzione cancellazioni</span>
                    <span className="font-mono font-bold text-amber-700">
                      {cancelDeltaPp > 0 ? `+${cancelDeltaPp}` : cancelDeltaPp} pp
                    </span>
                  </div>
                  <input
                    type="range"
                    min={-12}
                    max={6}
                    step={0.5}
                    value={cancelDeltaPp}
                    onChange={(e) => setCancelDeltaPp(Number(e.target.value))}
                    className="mt-3 w-full accent-amber-600"
                  />
                  <div className="mt-1 flex justify-between text-[10px] text-slate-400">
                    <span>-12 pp</span>
                    <span>Base: {pct(summary.cancellation_rate)}</span>
                    <span>+6 pp</span>
                  </div>
                </label>
              </div>

              {simulated && (
                <div className="mt-4 grid grid-cols-3 gap-3 rounded-xl bg-slate-900 p-4 text-white">
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-slate-400">Ricavo simulato</p>
                    <p className="mt-1 font-mono text-base font-bold tabular-nums sm:text-lg">
                      {eurCompact.format(simulated.simRevenue)}
                    </p>
                    <p
                      className={`text-xs font-medium ${
                        simulated.deltaRevenue >= 0 ? "text-teal-300" : "text-rose-300"
                      }`}
                    >
                      {simulated.deltaRevenue >= 0 ? "+" : ""}
                      {eurCompact.format(simulated.deltaRevenue)} ({pct(simulated.deltaPct)})
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-slate-400">ADR simulato</p>
                    <p className="mt-1 font-mono text-base font-bold tabular-nums sm:text-lg">
                      {eur.format(simulated.simAdr)}
                    </p>
                    <p className="text-xs text-slate-400">da {eur.format(summary.adr)}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-slate-400">RevPAR stimato</p>
                    <p className="mt-1 font-mono text-base font-bold tabular-nums sm:text-lg">
                      {eur.format(simulated.simRevpar)}
                    </p>
                    <p className="text-xs text-slate-400">cap. assunta</p>
                  </div>
                </div>
              )}
            </div>

            {/* Lead-time risk insight from DA evaluation */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs lg:col-span-5">
              <div className="mb-3 flex items-start justify-between gap-2">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">
                    Rischio Cancellazione per Lead-Time
                  </h2>
                  <p className="text-xs text-slate-500">
                    Evidenza DA sul dataset completo (r = 0,1848): le prenotazioni oltre 180g cancellano ~4,7× più dei last-minute.
                  </p>
                </div>
                <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-800">
                  Analisi DA
                </span>
              </div>

              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={LEAD_TIME_RISK_BUCKETS} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
                    <YAxis
                      domain={[0, 0.45]}
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
                    />
                    <Tooltip formatter={(val: number | string) => pct(Number(val))} />
                    <Bar dataKey="cancelRate" name="Tasso cancellazione" radius={[6, 6, 0, 0]}>
                      {LEAD_TIME_RISK_BUCKETS.map((b, i) => (
                        <Cell
                          key={b.bucket}
                          fill={i >= 3 ? "#e11d48" : i >= 1 ? "#f59e0b" : "#0d9488"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
