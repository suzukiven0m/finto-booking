import { useEffect, useMemo, useState } from "react";
import { ApiError, listBookings } from "../api/client";
import type { BookingQuery } from "../api/client";
import type { Booking, Page } from "../api/types";
import { IconAlert, IconDownload, IconLake, IconMountain, IconX } from "../components/Icons";

const MARKET_SEGMENTS = [
  "Aviation",
  "Complementary",
  "Corporate",
  "Direct",
  "Groups",
  "Offline TA/TO",
  "Online TA",
  "Undefined",
];

const eur = new Intl.NumberFormat("it-IT", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 2,
});

function leadRiskBadge(leadTime: number) {
  if (leadTime <= 7) {
    return { label: `${leadTime}g · Basso`, cls: "bg-teal-50 text-teal-700 border-teal-200" };
  }
  if (leadTime <= 90) {
    return { label: `${leadTime}g · Medio`, cls: "bg-amber-50 text-amber-700 border-amber-200" };
  }
  return { label: `${leadTime}g · Alto`, cls: "bg-rose-50 text-rose-700 border-rose-200" };
}

export default function Ricerca({
  propertyId,
  onChangePropertyId,
}: {
  propertyId: string;
  onChangePropertyId: (id: string) => void;
}) {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [isCanceled, setIsCanceled] = useState("");
  const [marketSegment, setMarketSegment] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  const [result, setResult] = useState<Page<Booking> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    const params: BookingQuery = {
      property_id: propertyId ? Number(propertyId) : null,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      is_canceled: isCanceled === "" ? undefined : isCanceled === "true",
      market_segment: marketSegment || undefined,
      page,
      page_size: pageSize,
    };

    listBookings(params)
      .then((r) => {
        if (!controller.signal.aborted) setResult(r);
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
  }, [propertyId, dateFrom, dateTo, isCanceled, marketSegment, page, pageSize]);

  function filter<T>(setter: (v: T) => void) {
    return (v: T) => {
      setter(v);
      setPage(1);
    };
  }

  const sliceStats = useMemo(() => {
    const rows = result?.data ?? [];
    if (!rows.length) return null;
    const canceled = rows.filter((b) => b.is_canceled).length;
    const valid = rows.filter((b) => !b.is_canceled && b.nights > 0 && b.adr > 0);
    const totalNights = valid.reduce((s, b) => s + b.nights, 0);
    const totalRev = valid.reduce((s, b) => s + b.adr * b.nights, 0);
    const avgAdr = totalNights > 0 ? totalRev / totalNights : 0;
    const highRisk = rows.filter((b) => b.lead_time > 90).length;
    return {
      count: rows.length,
      cancelPct: canceled / rows.length,
      avgAdr,
      totalRev,
      highRiskPct: highRisk / rows.length,
    };
  }, [result]);

  function exportCsv() {
    if (!result?.data.length) return;
    const headers = [
      "id",
      "property_id",
      "arrival_date",
      "nights",
      "adr",
      "is_canceled",
      "adults",
      "children",
      "babies",
      "country",
      "customer_type",
      "market_segment",
      "distribution_channel",
      "deposit_type",
      "lead_time",
    ];
    const escape = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const lines = [
      headers.join(","),
      ...result.data.map((b) => headers.map((h) => escape(b[h as keyof Booking])).join(",")),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `buby-bookings-p${page}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const selectClass =
    "rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-900 outline-none focus:border-teal-600 focus:bg-white";

  return (
    <div className="animate-enter space-y-5">
      {/* Quick preset chips + Filter Bar */}
      <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-xs">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="mr-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Preset:
            </span>
            {[
              {
                label: "Tutte",
                active: isCanceled === "" && marketSegment === "",
                run: () => {
                  setIsCanceled("");
                  setMarketSegment("");
                  setPage(1);
                },
              },
              {
                label: "Solo Direct",
                active: marketSegment === "Direct" && isCanceled === "",
                run: () => {
                  setMarketSegment("Direct");
                  setIsCanceled("");
                  setPage(1);
                },
              },
              {
                label: "Cancellate Online TA",
                active: marketSegment === "Online TA" && isCanceled === "true",
                run: () => {
                  setMarketSegment("Online TA");
                  setIsCanceled("true");
                  setPage(1);
                },
              },
              {
                label: "Confermate Corporate",
                active: marketSegment === "Corporate" && isCanceled === "false",
                run: () => {
                  setMarketSegment("Corporate");
                  setIsCanceled("false");
                  setPage(1);
                },
              },
            ].map((chip) => (
              <button
                key={chip.label}
                type="button"
                onClick={chip.run}
                className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                  chip.active
                    ? "bg-slate-900 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {chip.label}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={exportCsv}
            disabled={!result?.data.length}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-40"
          >
            <IconDownload size={14} />
            Esporta CSV (pagina)
          </button>
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Proprietà
            <select
              className={selectClass}
              value={propertyId}
              onChange={(e) => {
                onChangePropertyId(e.target.value);
                setPage(1);
              }}
            >
              <option value="">Entrambe</option>
              <option value="1">Buby Lago</option>
              <option value="2">Buby Montagna</option>
            </select>
          </label>

          <label className="flex flex-col gap-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Arrivo da
            <input
              type="date"
              className={selectClass}
              value={dateFrom}
              onChange={(e) => filter(setDateFrom)(e.target.value)}
            />
          </label>

          <label className="flex flex-col gap-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Arrivo a
            <input
              type="date"
              className={selectClass}
              value={dateTo}
              onChange={(e) => filter(setDateTo)(e.target.value)}
            />
          </label>

          <label className="flex flex-col gap-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Stato
            <select
              className={selectClass}
              value={isCanceled}
              onChange={(e) => filter(setIsCanceled)(e.target.value)}
            >
              <option value="">Tutte</option>
              <option value="false">Confermate</option>
              <option value="true">Cancellate</option>
            </select>
          </label>

          <label className="flex flex-col gap-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Segmento
            <select
              className={selectClass}
              value={marketSegment}
              onChange={(e) => filter(setMarketSegment)(e.target.value)}
            >
              <option value="">Tutti</option>
              {MARKET_SEGMENTS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Righe/pag.
            <select
              className={selectClass}
              value={pageSize}
              onChange={(e) => filter(setPageSize)(Number(e.target.value))}
            >
              {[25, 50, 100, 200].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      {/* Slice Intelligence Summary */}
      {sliceStats && !loading && (
        <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-xl border border-slate-200/80 bg-white px-4 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Totale nel DB (filtrato)
            </p>
            <p className="mt-1 font-mono text-lg font-bold text-slate-900 tabular-nums">
              {result?.meta.total.toLocaleString("it-IT")}
            </p>
          </div>
          <div className="rounded-xl border border-slate-200/80 bg-white px-4 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              ADR medio (pagina)
            </p>
            <p className="mt-1 font-mono text-lg font-bold text-teal-700 tabular-nums">
              {eur.format(sliceStats.avgAdr)}
            </p>
          </div>
          <div className="rounded-xl border border-slate-200/80 bg-white px-4 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Cancellate (pagina)
            </p>
            <p className="mt-1 font-mono text-lg font-bold text-rose-600 tabular-nums">
              {Math.round(sliceStats.cancelPct * 100)}%
            </p>
          </div>
          <div className="rounded-xl border border-slate-200/80 bg-white px-4 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Lead time &gt; 90g (pagina)
            </p>
            <p className="mt-1 font-mono text-lg font-bold text-amber-600 tabular-nums">
              {Math.round(sliceStats.highRiskPct * 100)}%
            </p>
          </div>
        </section>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <IconAlert size={16} />
          {error}
        </div>
      )}

      {loading && (
        <div className="rounded-2xl border border-slate-200 bg-white py-16 text-center text-sm text-slate-500">
          Caricamento prenotazioni…
        </div>
      )}

      {!loading && result && result.data.length === 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white py-12 text-center text-sm text-slate-500">
          Nessuna prenotazione trovata con i filtri selezionati.
        </div>
      )}

      {!loading && result && result.data.length > 0 && (
        <>
          <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs">
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead className="border-b border-slate-200 bg-slate-50/80">
                  <tr>
                    {[
                      "ID",
                      "Struttura",
                      "Arrivo",
                      "Notti",
                      "ADR",
                      "Valore",
                      "Stato",
                      "Ospiti",
                      "Paese",
                      "Segmento",
                      "Rischio Lead",
                    ].map((h) => (
                      <th
                        key={h}
                        className="px-3.5 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {result.data.map((b: Booking) => {
                    const risk = leadRiskBadge(b.lead_time);
                    const totalGuests = b.adults + b.children + b.babies;
                    return (
                      <tr
                        key={b.id}
                        onClick={() => setSelectedBooking(b)}
                        className="cursor-pointer transition-colors hover:bg-teal-50/40"
                      >
                        <td className="px-3.5 py-2.5 font-mono text-slate-400">#{b.id}</td>
                        <td className="px-3.5 py-2.5 font-medium text-slate-800">
                          <span className="inline-flex items-center gap-1.5">
                            {b.property_id === 1 ? (
                              <IconLake size={13} className="text-teal-600" />
                            ) : (
                              <IconMountain size={13} className="text-amber-600" />
                            )}
                            {b.property_id === 1 ? "Lago" : "Montagna"}
                          </span>
                        </td>
                        <td className="px-3.5 py-2.5 font-mono tabular-nums text-slate-700">
                          {b.arrival_date}
                        </td>
                        <td className="px-3.5 py-2.5 font-mono tabular-nums">{b.nights}</td>
                        <td className="px-3.5 py-2.5 font-mono tabular-nums">{eur.format(b.adr)}</td>
                        <td className="px-3.5 py-2.5 font-mono font-semibold tabular-nums text-slate-900">
                          {b.is_canceled ? "—" : eur.format(b.adr * b.nights)}
                        </td>
                        <td className="px-3.5 py-2.5">
                          {b.is_canceled ? (
                            <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-semibold text-rose-700">
                              Cancellata
                            </span>
                          ) : (
                            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                              Valida
                            </span>
                          )}
                        </td>
                        <td className="px-3.5 py-2.5 tabular-nums text-slate-600">{totalGuests}</td>
                        <td className="px-3.5 py-2.5 font-mono text-slate-600">
                          {b.country ?? "—"}
                        </td>
                        <td className="px-3.5 py-2.5 font-medium text-slate-700">
                          {b.market_segment}
                        </td>
                        <td className="px-3.5 py-2.5">
                          <span
                            className={`inline-block rounded-full border px-2 py-0.5 font-mono text-[10px] font-semibold ${risk.cls}`}
                          >
                            {risk.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
            <span>
              {result.meta.total.toLocaleString("it-IT")} prenotazioni totali · pagina{" "}
              <strong>{page}</strong> di <strong>{result.meta.total_pages}</strong> (clicca una riga per i dettagli)
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="rounded-xl border border-slate-200 bg-white px-3.5 py-1.5 font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-40"
              >
                ‹ Prec.
              </button>
              <button
                type="button"
                disabled={page >= result.meta.total_pages}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-xl border border-slate-200 bg-white px-3.5 py-1.5 font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-40"
              >
                Succ. ›
              </button>
            </div>
          </div>
        </>
      )}

      {/* Detail Slide-Over Drawer */}
      {selectedBooking && (
        <div
          className="fixed inset-0 z-50 flex justify-end bg-slate-950/40 backdrop-blur-xs"
          onClick={() => setSelectedBooking(null)}
          role="dialog"
          aria-modal="true"
          aria-label={`Dettaglio prenotazione ${selectedBooking.id}`}
        >
          <div
            className="animate-enter flex h-full w-full max-w-md flex-col justify-between bg-white p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="space-y-5 overflow-y-auto">
              <div className="flex items-start justify-between border-b border-slate-100 pb-4">
                <div>
                  <span className="font-mono text-xs text-slate-400">
                    Booking #{selectedBooking.id}
                  </span>
                  <h3 className="mt-0.5 text-lg font-bold text-slate-900">
                    {selectedBooking.property_id === 1 ? "Buby Lago" : "Buby Montagna"}
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedBooking(null)}
                  className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                >
                  <IconX size={18} />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-[10px] font-semibold uppercase text-slate-400">Arrivo</p>
                  <p className="mt-1 font-mono text-sm font-bold text-slate-900">
                    {selectedBooking.arrival_date}
                  </p>
                </div>
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-[10px] font-semibold uppercase text-slate-400">Valore soggiorno</p>
                  <p className="mt-1 font-mono text-sm font-bold text-teal-700">
                    {eur.format(selectedBooking.adr * selectedBooking.nights)}
                  </p>
                </div>
              </div>

              <dl className="divide-y divide-slate-100 text-xs">
                {[
                  ["Stato", selectedBooking.is_canceled ? "Cancellata" : "Valida / Non cancellata"],
                  ["Notti", `${selectedBooking.nights} notti`],
                  ["ADR", eur.format(selectedBooking.adr)],
                  [
                    "Ospiti",
                    `${selectedBooking.adults} adulti, ${selectedBooking.children} bambini, ${selectedBooking.babies} neonati`,
                  ],
                  ["Paese (ISO-3)", selectedBooking.country ?? "Non specificato"],
                  ["Segmento mercato", selectedBooking.market_segment],
                  ["Canale distribuzione", selectedBooking.distribution_channel],
                  ["Tipo deposito", selectedBooking.deposit_type],
                  ["Tipo cliente", selectedBooking.customer_type],
                  ["Lead time", `${selectedBooking.lead_time} giorni`],
                ].map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between py-2.5">
                    <dt className="text-slate-500">{k}</dt>
                    <dd className="font-semibold text-slate-900">{v}</dd>
                  </div>
                ))}
              </dl>
            </div>

            <button
              type="button"
              onClick={() => setSelectedBooking(null)}
              className="mt-4 w-full rounded-xl bg-slate-900 py-2.5 text-xs font-semibold text-white hover:bg-slate-800"
            >
              Chiudi scheda
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
