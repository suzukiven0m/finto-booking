import { useEffect, useState } from "react";
import { ApiError, listBookings } from "../api/client";
import type { BookingQuery } from "../api/client";
import type { Booking, Page } from "../api/types";

// Eight market segments from the CSV (spec: MarketSegment parameter description)
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

export default function Ricerca() {
  const [propertyId, setPropertyId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [isCanceled, setIsCanceled] = useState("");
  const [marketSegment, setMarketSegment] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  const [result, setResult] = useState<Page<Booking> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
            : "Impossibile raggiungere l'API. Mock attivo (npm run mock)?",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [propertyId, dateFrom, dateTo, isCanceled, marketSegment, page, pageSize]);

  // Reset to page 1 when any filter changes
  function filter<T>(setter: (v: T) => void) {
    return (v: T) => {
      setter(v);
      setPage(1);
    };
  }

  const selectClass =
    "rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";
  const inputClass = "rounded-md border border-slate-300 bg-white px-3 py-2 text-sm";

  return (
    <div>
      {/* Filters — exactly the declared spec parameters */}
      <div className="mb-5 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
          Proprietà
          <select
            className={selectClass}
            value={propertyId}
            onChange={(e) => filter(setPropertyId)(e.target.value)}
          >
            <option value="">Entrambe</option>
            <option value="1">Buby Lago</option>
            <option value="2">Buby Montagna</option>
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
          Arrivo da
          <input
            type="date"
            className={inputClass}
            value={dateFrom}
            onChange={(e) => filter(setDateFrom)(e.target.value)}
          />
        </label>

        <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
          Arrivo a
          <input
            type="date"
            className={inputClass}
            value={dateTo}
            onChange={(e) => filter(setDateTo)(e.target.value)}
          />
        </label>

        <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
          Cancellata
          <select
            className={selectClass}
            value={isCanceled}
            onChange={(e) => filter(setIsCanceled)(e.target.value)}
          >
            <option value="">Tutte</option>
            <option value="false">No</option>
            <option value="true">Sì</option>
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
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

        <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
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

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <p className="py-16 text-center text-sm text-slate-500">Caricamento prenotazioni…</p>
      )}

      {!loading && result && result.data.length === 0 && (
        <p className="py-8 text-center text-sm text-slate-500">
          Nessuna prenotazione trovata con i filtri selezionati.
        </p>
      )}

      {!loading && result && result.data.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full text-xs">
              <thead className="border-b border-slate-200 bg-slate-50">
                <tr>
                  {[
                    "ID",
                    "Prop.",
                    "Arrivo",
                    "Notti",
                    "ADR",
                    "Cancel.",
                    "Adulti",
                    "Paese",
                    "Segmento",
                    "Lead time",
                  ].map((h) => (
                    <th
                      key={h}
                      className="px-3 py-2 text-left font-medium uppercase tracking-wide text-slate-500"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {result.data.map((b: Booking) => (
                  <tr key={b.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-500">{b.id}</td>
                    <td className="px-3 py-2">{b.property_id === 1 ? "Lago" : "Montagna"}</td>
                    <td className="px-3 py-2 tabular-nums">{b.arrival_date}</td>
                    <td className="px-3 py-2 tabular-nums">{b.nights}</td>
                    <td className="px-3 py-2 tabular-nums">{eur.format(b.adr)}</td>
                    <td className="px-3 py-2">
                      {b.is_canceled ? (
                        <span className="rounded-full bg-red-100 px-2 py-0.5 text-red-700">
                          Sì
                        </span>
                      ) : (
                        <span className="rounded-full bg-green-100 px-2 py-0.5 text-green-700">
                          No
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 tabular-nums">{b.adults}</td>
                    <td className="px-3 py-2">{b.country ?? "—"}</td>
                    <td className="px-3 py-2">{b.market_segment}</td>
                    <td className="px-3 py-2 tabular-nums">{b.lead_time}g</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination controls + meta */}
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
            <span>
              {result.meta.total.toLocaleString("it-IT")} prenotazioni totali · pagina {page} di{" "}
              {result.meta.total_pages}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="rounded-md border border-slate-300 bg-white px-3 py-1 font-medium disabled:opacity-40 hover:bg-slate-100"
              >
                ‹ Prec.
              </button>
              <button
                type="button"
                disabled={page >= result.meta.total_pages}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-md border border-slate-300 bg-white px-3 py-1 font-medium disabled:opacity-40 hover:bg-slate-100"
              >
                Succ. ›
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
