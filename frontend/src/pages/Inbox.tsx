import { useEffect, useMemo, useState } from "react";
import { ApiError, listGuestRequests, patchGuestRequest } from "../api/client";
import type { GuestRequest, Page } from "../api/types";
import {
  IconAlert,
  IconCheck,
  IconSearch,
  IconSend,
  IconShield,
  IconSparkles,
} from "../components/Icons";
import { EMAIL_CLASSIFIER_BENCHMARK } from "../data/corpusInsights";
import type { Session } from "../session";

const CATEGORY_META: Record<
  string,
  { label: string; badge: string; priority: "Alta" | "Media" | "Normale"; template: (prop: string) => string }
> = {
  complaint: {
    label: "Reclamo",
    badge: "bg-rose-100 text-rose-800 border-rose-200",
    priority: "Alta",
    template: (prop) =>
      `Gentile Ospite,\nci scusiamo sinceramente per il disagio segnalato durante il Suo soggiorno presso ${prop}. Il nostro team di direzione sta già verificando l'accaduto per offrirLe un riscontro concreto. Restiamo a completa disposizione.`,
  },
  cancellation: {
    label: "Cancellazione",
    badge: "bg-amber-100 text-amber-800 border-amber-200",
    priority: "Alta",
    template: (prop) =>
      `Gentile Ospite,\nabbiamo preso in carico la Sua richiesta di modifica/cancellazione per ${prop}. In base alle condizioni della tariffa prenotata, Le confermiamo che procederemo secondo la policy applicabile. Cordiali saluti.`,
  },
  availability: {
    label: "Disponibilità",
    badge: "bg-teal-100 text-teal-800 border-teal-200",
    priority: "Media",
    template: (prop) =>
      `Gentile Ospite,\ngrazie per aver contattato ${prop}. Confermiamo la disponibilità per le date indicate. Può completare la prenotazione diretta con la miglior tariffa garantita rispondendo a questa email.`,
  },
  billing: {
    label: "Fatturazione",
    badge: "bg-indigo-100 text-indigo-800 border-indigo-200",
    priority: "Media",
    template: (prop) =>
      `Gentile Ospite,\nin merito alla Sua richiesta amministrativa per il soggiorno presso ${prop}, il nostro ufficio contabilità sta predisponendo il documento richiesto che riceverà a stretto giro.`,
  },
  special_request: {
    label: "Richiesta speciale",
    badge: "bg-sky-100 text-sky-800 border-sky-200",
    priority: "Normale",
    template: (prop) =>
      `Gentile Ospite,\nsaremo lieti di accogliere la Sua richiesta speciale presso ${prop} e abbiamo già informato il reparto ricevimento per preparare al meglio il Suo arrivo.`,
  },
  info: {
    label: "Informazioni",
    badge: "bg-slate-100 text-slate-700 border-slate-200",
    priority: "Normale",
    template: (prop) =>
      `Gentile Ospite,\ngrazie per averci scritto. Ecco tutte le informazioni richieste relative ai servizi di ${prop}. Restiamo a disposizione per qualsiasi altra esigenza.`,
  },
};

function StatusBadge({ status }: { status: GuestRequest["status"] }) {
  const styles: Record<GuestRequest["status"], string> = {
    new: "bg-sky-100 text-sky-800",
    draft: "bg-amber-100 text-amber-800",
    sent: "bg-emerald-100 text-emerald-800",
  };
  const labels: Record<GuestRequest["status"], string> = {
    new: "Nuova",
    draft: "Bozza pronta",
    sent: "Inviata",
  };
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

export default function Inbox({
  session,
  propertyId,
  onChangePropertyId,
}: {
  session: Session;
  propertyId: string;
  onChangePropertyId: (id: string) => void;
}) {
  const [statusFilter, setStatusFilter] = useState<"" | "new" | "draft" | "sent">("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(1);

  const [result, setResult] = useState<Page<GuestRequest> | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const [selected, setSelected] = useState<GuestRequest | null>(null);
  const [editDraft, setEditDraft] = useState("");
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // property_manager may read but not write (role matrix, pre-freeze 2026-11-19)
  const isPropertyManager = session.role === "property_manager";

  useEffect(() => {
    const controller = new AbortController();
    setListLoading(true);
    setListError(null);

    listGuestRequests({
      property_id: propertyId ? Number(propertyId) : null,
      status: statusFilter || undefined,
      page,
      page_size: 50,
    })
      .then((r) => {
        if (controller.signal.aborted) return;
        setResult(r);
        setSelected((prev) => {
          if (!prev) return r.data[0] ?? null;
          const updated = r.data.find((x) => x.id === prev.id);
          return updated ?? prev;
        });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setListError(
          err instanceof ApiError
            ? `${err.message} (${err.code})`
            : "Impossibile raggiungere l'API. Verifica backend o mock.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setListLoading(false);
      });

    return () => controller.abort();
  }, [propertyId, statusFilter, page]);

  useEffect(() => {
    if (selected) {
      setEditDraft(selected.draft_reply ?? "");
    }
  }, [selected?.id]);

  const visibleItems = useMemo(() => {
    const items = result?.data ?? [];
    const q = searchQuery.trim().toLowerCase();
    return items.filter((r) => {
      if (categoryFilter && r.category !== categoryFilter) return false;
      if (!q) return true;
      return (
        r.body.toLowerCase().includes(q) ||
        (r.category ?? "").toLowerCase().includes(q) ||
        String(r.id).includes(q)
      );
    });
  }, [result, categoryFilter, searchQuery]);

  const counts = useMemo(() => {
    const items = result?.data ?? [];
    return {
      newCount: items.filter((i) => i.status === "new").length,
      draftCount: items.filter((i) => i.status === "draft").length,
      sentCount: items.filter((i) => i.status === "sent").length,
    };
  }, [result]);

  function selectItem(r: GuestRequest) {
    setSelected(r);
    setEditDraft(r.draft_reply ?? "");
    setActionError(null);
    setActionSuccess(null);
  }

  function patchAndSync(
    id: number,
    body: Parameters<typeof patchGuestRequest>[1],
    successMsg: string,
  ) {
    setSaving(true);
    setActionError(null);
    setActionSuccess(null);
    return patchGuestRequest(id, body)
      .then((updated) => {
        setSelected(updated);
        setEditDraft(updated.draft_reply ?? "");
        setResult((prev) =>
          prev
            ? { ...prev, data: prev.data.map((r) => (r.id === updated.id ? updated : r)) }
            : prev,
        );
        setActionSuccess(successMsg);
      })
      .catch((err: unknown) => {
        const msg =
          err instanceof ApiError && err.status === 403
            ? "Il tuo ruolo non può eseguire questa azione (403 Forbidden)."
            : err instanceof ApiError
              ? `${err.message} (${err.code})`
              : "Errore API.";
        setActionError(msg);
      })
      .finally(() => setSaving(false));
  }

  function handleSaveDraft() {
    if (!selected) return;
    // Saving draft reply only — does not change status
    void patchAndSync(selected.id, { draft_reply: editDraft }, "Bozza salvata sul server.");
  }

  function handleSend() {
    // ONLY from draft status; never automatic
    if (!selected || selected.status !== "draft") return;
    void patchAndSync(
      selected.id,
      { status: "sent" },
      "Risposta approvata e marcata come inviata (HITL).",
    );
  }

  function applyCategoryTemplate() {
    if (!selected) return;
    const propName = selected.property_id === 1 ? "Buby Lago" : "Buby Montagna";
    const meta = selected.category ? CATEGORY_META[selected.category] : undefined;
    const text = meta
      ? meta.template(propName)
      : `Gentile Ospite,\ngrazie per aver contattato ${propName}. Abbiamo ricevuto la Sua richiesta e Le risponderemo al più presto.`;
    setEditDraft(text);
    setActionSuccess(null);
  }

  const hasUnsavedChanges = selected ? editDraft !== (selected.draft_reply ?? "") : false;

  return (
    <div className="animate-enter space-y-5">
      {/* Synthetic disclosure + Pipeline Stats */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-amber-200 bg-amber-50/70 px-4 py-3 text-xs text-amber-900">
        <div className="flex items-center gap-2">
          <IconShield size={16} className="shrink-0 text-amber-700" />
          <span>
            <strong>Inbox HITL (Human-in-the-loop):</strong> email <strong>sintetiche</strong>{" "}
            ({EMAIL_CLASSIFIER_BENCHMARK.syntheticTotal} generate, F1 cat.{" "}
            {(EMAIL_CLASSIFIER_BENCHMARK.categoryMacroF1 * 100).toFixed(1)}%). Nessuna risposta
            parte senza approvazione umana esplicita.
          </span>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="rounded-full bg-white px-2 py-0.5 text-sky-700">
            Nuove: {counts.newCount}
          </span>
          <span className="rounded-full bg-white px-2 py-0.5 text-amber-700">
            Bozze: {counts.draftCount}
          </span>
          <span className="rounded-full bg-white px-2 py-0.5 text-emerald-700">
            Inviate: {counts.sentCount}
          </span>
        </div>
      </div>

      {/* Filter Ribbon */}
      <section className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200/80 bg-white p-3.5 shadow-xs">
        <div className="flex flex-wrap items-center gap-2">
          <select
            aria-label="Filtra proprietà inbox"
            className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-800"
            value={propertyId}
            onChange={(e) => {
              onChangePropertyId(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Tutte le strutture</option>
            <option value="1">Buby Lago</option>
            <option value="2">Buby Montagna</option>
          </select>

          <select
            aria-label="Filtra stato inbox"
            className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-800"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as typeof statusFilter);
              setPage(1);
            }}
          >
            <option value="">Tutti gli stati</option>
            <option value="new">Nuova</option>
            <option value="draft">Bozza pronta</option>
            <option value="sent">Inviata</option>
          </select>

          <select
            aria-label="Filtra categoria inbox"
            className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-800"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">Tutte le categorie</option>
            {Object.entries(CATEGORY_META).map(([k, m]) => (
              <option key={k} value={k}>
                {m.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5">
          <IconSearch size={14} className="text-slate-400" />
          <input
            type="text"
            placeholder="Cerca testo email o #id…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-44 bg-transparent text-xs text-slate-800 outline-none placeholder:text-slate-400"
          />
        </div>
      </section>

      {/* Split Workspace */}
      <div className="grid gap-5 lg:grid-cols-12">
        {/* List Pane */}
        <div className="space-y-2.5 lg:col-span-5">
          {listError && (
            <div className="flex items-center gap-2 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <IconAlert size={16} />
              {listError}
            </div>
          )}

          {listLoading && (
            <div className="rounded-2xl border border-slate-200 bg-white py-12 text-center text-sm text-slate-500">
              Caricamento inbox…
            </div>
          )}

          {!listLoading && visibleItems.length === 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white py-12 text-center text-sm text-slate-500">
              Nessuna richiesta trovata con questi filtri.
            </div>
          )}

          {!listLoading && visibleItems.length > 0 && (
            <>
              <div className="max-h-[600px] space-y-2 overflow-y-auto pr-1">
                {visibleItems.map((r) => {
                  const cat = r.category ? CATEGORY_META[r.category] : undefined;
                  const isActive = selected?.id === r.id;
                  return (
                    <button
                      key={r.id}
                      type="button"
                      onClick={() => selectItem(r)}
                      className={`w-full rounded-2xl border p-3.5 text-left transition ${
                        isActive
                          ? "border-teal-500 bg-white ring-2 ring-teal-500/20 shadow-sm"
                          : "border-slate-200/80 bg-white/80 hover:bg-white hover:shadow-xs"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-slate-900">#{r.id}</span>
                          {cat && (
                            <span
                              className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${cat.badge}`}
                            >
                              {cat.label}
                            </span>
                          )}
                        </div>
                        <StatusBadge status={r.status} />
                      </div>
                      <p className="mt-1 text-[11px] text-slate-400">
                        {r.received_at.slice(0, 10)} ·{" "}
                        {r.property_id === 1 ? "Buby Lago" : "Buby Montagna"}
                      </p>
                      <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-slate-700">
                        {r.body}
                      </p>
                    </button>
                  );
                })}
              </div>

              {result && result.meta.total_pages > 1 && (
                <div className="flex items-center justify-between pt-1 text-xs text-slate-500">
                  <span>
                    {result.meta.total} richieste · pag. {page}/{result.meta.total_pages}
                  </span>
                  <div className="flex gap-1.5">
                    <button
                      type="button"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => p - 1)}
                      className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 font-medium hover:bg-slate-50 disabled:opacity-40"
                    >
                      ‹ Prec.
                    </button>
                    <button
                      type="button"
                      disabled={page >= result.meta.total_pages}
                      onClick={() => setPage((p) => p + 1)}
                      className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 font-medium hover:bg-slate-50 disabled:opacity-40"
                    >
                      Succ. ›
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Detail & Co-Pilot Pane */}
        <div className="lg:col-span-7">
          {!selected ? (
            <div className="flex h-72 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/60 text-sm text-slate-400">
              Seleziona una richiesta dall'elenco per ispezionarla.
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
              <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 pb-4">
                <span className="font-mono text-base font-bold text-slate-900">
                  Richiesta #{selected.id}
                </span>
                <StatusBadge status={selected.status} />
                {selected.category && (
                  <span
                    className={`rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${
                      CATEGORY_META[selected.category]?.badge ??
                      "border-slate-200 bg-slate-100 text-slate-700"
                    }`}
                  >
                    {CATEGORY_META[selected.category]?.label ?? selected.category}
                  </span>
                )}
                {selected.category && CATEGORY_META[selected.category]?.priority === "Alta" && (
                  <span className="rounded-full bg-rose-600 px-2 py-0.5 text-[10px] font-bold uppercase text-white">
                    Priorità Alta
                  </span>
                )}
                <span className="ml-auto font-mono text-xs text-slate-400">
                  {selected.received_at.slice(0, 16).replace("T", " ")} ·{" "}
                  {selected.property_id === 1 ? "Buby Lago" : "Buby Montagna"}
                </span>
              </div>

              {/* Original guest message */}
              <div className="mt-4">
                <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Messaggio originale ospite
                </p>
                <div className="rounded-xl border border-slate-200/70 bg-slate-50 p-4 text-sm leading-relaxed text-slate-800">
                  {selected.body}
                </div>
              </div>

              {/* Terminal sent view */}
              {selected.status === "sent" ? (
                <div className="mt-5 space-y-3">
                  {selected.draft_reply && (
                    <div>
                      <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-emerald-700">
                        Risposta approvata e inviata
                      </p>
                      <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 text-sm leading-relaxed text-slate-800">
                        {selected.draft_reply}
                      </div>
                    </div>
                  )}
                  <p className="flex items-center gap-1.5 text-xs text-slate-400">
                    <IconCheck size={14} className="text-emerald-600" />
                    Stato terminale — nessuna ulteriore modifica consentita.
                  </p>
                </div>
              ) : isPropertyManager ? (
                <div className="mt-5 space-y-3">
                  {selected.draft_reply && (
                    <div>
                      <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                        Bozza proposta (sola lettura)
                      </p>
                      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-800">
                        {selected.draft_reply}
                      </div>
                    </div>
                  )}
                  <p className="rounded-xl border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-xs text-amber-800">
                    Il ruolo <strong>property_manager</strong> è abilitato alla sola lettura (403 Forbidden su PATCH).
                  </p>
                </div>
              ) : (
                <div className="mt-5 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Bozza risposta assistente (revisione umana obbligatoria)
                    </label>
                    <button
                      type="button"
                      onClick={applyCategoryTemplate}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-teal-200 bg-teal-50 px-2.5 py-1 text-[11px] font-semibold text-teal-800 transition hover:bg-teal-100"
                    >
                      <IconSparkles size={13} />
                      Inserisci template suggerito
                    </button>
                  </div>

                  <textarea
                    rows={6}
                    className="w-full rounded-xl border border-slate-300 bg-white p-3.5 text-sm leading-relaxed text-slate-900 outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-600/15"
                    value={editDraft}
                    onChange={(e) => {
                      setEditDraft(e.target.value);
                      setActionSuccess(null);
                    }}
                    disabled={saving}
                    placeholder="Scrivi o modifica la bozza di risposta…"
                  />

                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      <span>{editDraft.length} caratteri</span>
                      {hasUnsavedChanges && (
                        <span className="font-semibold text-amber-600">Modifiche non salvate</span>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={handleSaveDraft}
                        disabled={saving}
                        className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-800 transition hover:bg-slate-50 disabled:opacity-50"
                      >
                        Salva bozza
                      </button>

                      {selected.status === "draft" && (
                        <button
                          type="button"
                          onClick={handleSend}
                          disabled={saving || hasUnsavedChanges}
                          title={
                            hasUnsavedChanges
                              ? "Salva prima le modifiche alla bozza"
                              : "Approva e invia risposta"
                          }
                          className="inline-flex items-center gap-1.5 rounded-xl bg-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-xs transition hover:bg-teal-700 disabled:opacity-50"
                        >
                          <IconSend size={14} />
                          Approva e invia
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {actionSuccess && (
                <p className="mt-3 flex items-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50 px-3.5 py-2 text-xs font-medium text-emerald-800">
                  <IconCheck size={14} />
                  {actionSuccess}
                </p>
              )}

              {actionError && (
                <p className="mt-3 flex items-center gap-1.5 rounded-xl border border-red-200 bg-red-50 px-3.5 py-2 text-xs font-medium text-red-700">
                  <IconAlert size={14} />
                  {actionError}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
