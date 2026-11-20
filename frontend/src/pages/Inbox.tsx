import { useEffect, useState } from "react";
import { ApiError, listGuestRequests, patchGuestRequest } from "../api/client";
import type { GuestRequest, Page } from "../api/types";
import type { Session } from "../session";

function StatusBadge({ status }: { status: GuestRequest["status"] }) {
  const styles: Record<GuestRequest["status"], string> = {
    new: "bg-blue-100 text-blue-700",
    draft: "bg-amber-100 text-amber-700",
    sent: "bg-green-100 text-green-700",
  };
  const labels: Record<GuestRequest["status"], string> = {
    new: "Nuova",
    draft: "Bozza",
    sent: "Inviata",
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

export default function Inbox({ session }: { session: Session }) {
  const [propertyId, setPropertyId] = useState("");
  const [statusFilter, setStatusFilter] = useState<"" | "new" | "draft" | "sent">("");
  const [page, setPage] = useState(1);

  const [result, setResult] = useState<Page<GuestRequest> | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const [selected, setSelected] = useState<GuestRequest | null>(null);
  const [editDraft, setEditDraft] = useState("");
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

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
        // Keep selected item in sync if it appears in the new page
        setSelected((prev) => {
          if (!prev) return prev;
          const updated = r.data.find((x) => x.id === prev.id);
          return updated ?? prev;
        });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setListError(
          err instanceof ApiError
            ? `${err.message} (${err.code})`
            : "Impossibile raggiungere l'API. Mock attivo (npm run mock)?",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setListLoading(false);
      });

    return () => controller.abort();
  }, [propertyId, statusFilter, page]);

  function selectItem(r: GuestRequest) {
    setSelected(r);
    setEditDraft(r.draft_reply ?? "");
    setActionError(null);
  }

  function patchAndSync(id: number, body: Parameters<typeof patchGuestRequest>[1]) {
    setSaving(true);
    setActionError(null);
    return patchGuestRequest(id, body)
      .then((updated) => {
        setSelected(updated);
        setResult((prev) =>
          prev
            ? { ...prev, data: prev.data.map((r) => (r.id === updated.id ? updated : r)) }
            : prev,
        );
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
    void patchAndSync(selected.id, { draft_reply: editDraft });
  }

  function handleSend() {
    // ONLY from draft status; never automatic
    if (!selected || selected.status !== "draft") return;
    void patchAndSync(selected.id, { status: "sent" });
  }

  const selectClass =
    "rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";

  return (
    <div>
      {/* Synthetic-email disclosure (D20 requirement) */}
      <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800">
        <strong>Nota:</strong> le email degli ospiti sono <strong>sintetiche</strong> (generatore
        DA-3), non corrispondenza reale. Una persona approva esplicitamente prima di qualsiasi
        invio — non ci sono invii automatici.
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
          Proprietà
          <select
            className={selectClass}
            value={propertyId}
            onChange={(e) => {
              setPropertyId(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Tutte</option>
            <option value="1">Buby Lago</option>
            <option value="2">Buby Montagna</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
          Stato
          <select
            className={selectClass}
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as typeof statusFilter);
              setPage(1);
            }}
          >
            <option value="">Tutti</option>
            <option value="new">Nuova</option>
            <option value="draft">Bozza</option>
            <option value="sent">Inviata</option>
          </select>
        </label>
      </div>

      <div className="flex gap-4">
        {/* List pane */}
        <div className="w-1/2 min-w-0">
          {listError && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {listError}
            </div>
          )}

          {listLoading && (
            <p className="py-8 text-center text-sm text-slate-500">Caricamento inbox…</p>
          )}

          {!listLoading && result && result.data.length === 0 && (
            <p className="py-8 text-center text-sm text-slate-500">Nessuna richiesta trovata.</p>
          )}

          {!listLoading && result && result.data.length > 0 && (
            <div className="space-y-2">
              {result.data.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => selectItem(r)}
                  className={`w-full rounded-lg border p-3 text-left ${
                    selected?.id === r.id
                      ? "border-sky-300 bg-sky-50"
                      : "border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-slate-900">
                      #{r.id}{r.category ? ` — ${r.category}` : ""}
                    </span>
                    <StatusBadge status={r.status} />
                  </div>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {r.received_at.slice(0, 10)} ·{" "}
                    {r.property_id === 1 ? "Buby Lago" : "Buby Montagna"}
                  </p>
                  <p className="mt-1 line-clamp-2 text-xs text-slate-700">
                    {r.body.slice(0, 100)}
                    {r.body.length > 100 ? "…" : ""}
                  </p>
                </button>
              ))}

              {result.meta.total_pages > 1 && (
                <div className="flex items-center justify-between gap-3 pt-2 text-xs text-slate-500">
                  <span>
                    {result.meta.total} richieste · p. {page}/{result.meta.total_pages}
                  </span>
                  <div className="flex gap-1">
                    <button
                      type="button"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => p - 1)}
                      className="rounded border border-slate-300 bg-white px-2 py-1 disabled:opacity-40 hover:bg-slate-100"
                    >
                      ‹
                    </button>
                    <button
                      type="button"
                      disabled={page >= result.meta.total_pages}
                      onClick={() => setPage((p) => p + 1)}
                      className="rounded border border-slate-300 bg-white px-2 py-1 disabled:opacity-40 hover:bg-slate-100"
                    >
                      ›
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Detail pane */}
        <div className="w-1/2 min-w-0">
          {!selected && (
            <p className="py-8 text-center text-sm text-slate-500">
              Seleziona una richiesta dall'elenco.
            </p>
          )}

          {selected && (
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              {/* Header */}
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <span className="text-sm font-semibold text-slate-900">#{selected.id}</span>
                <StatusBadge status={selected.status} />
                {selected.category && (
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                    {selected.category}
                  </span>
                )}
                <span className="ml-auto text-xs text-slate-400">
                  {selected.received_at.slice(0, 16).replace("T", " ")}
                </span>
              </div>

              {/* Email body */}
              <div className="mb-4 rounded-md bg-slate-50 p-3 text-sm text-slate-800">
                {selected.body}
              </div>

              {/* Sent state: reply shown read-only, all actions disabled */}
              {selected.status === "sent" && (
                <>
                  {selected.draft_reply && (
                    <div className="mb-3">
                      <p className="mb-1 text-xs font-medium text-slate-500">Risposta inviata</p>
                      <div className="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-slate-800">
                        {selected.draft_reply}
                      </div>
                    </div>
                  )}
                  <p className="text-xs text-slate-400">
                    Stato terminale — nessuna azione disponibile.
                  </p>
                </>
              )}

              {/* New / draft state */}
              {selected.status !== "sent" && (
                <>
                  {/* property_manager: read-only view + permission note */}
                  {isPropertyManager ? (
                    <div>
                      {selected.draft_reply && (
                        <div className="mb-3">
                          <p className="mb-1 text-xs font-medium text-slate-500">
                            Bozza risposta (sola lettura)
                          </p>
                          <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-800">
                            {selected.draft_reply}
                          </div>
                        </div>
                      )}
                      <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                        Il ruolo <strong>property_manager</strong> non ha i permessi di scrittura
                        su questa risorsa (403 Forbidden per PATCH).
                      </p>
                    </div>
                  ) : (
                    /* admin / manager: edit draft + send */
                    <div>
                      <label className="mb-1 block text-xs font-medium text-slate-500">
                        Bozza risposta
                      </label>
                      <textarea
                        rows={5}
                        className="w-full rounded-md border border-slate-300 p-2 text-sm text-slate-900"
                        value={editDraft}
                        onChange={(e) => setEditDraft(e.target.value)}
                        disabled={saving}
                      />

                      <div className="mt-2 flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={handleSaveDraft}
                          disabled={saving}
                          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium disabled:opacity-50 hover:bg-slate-100"
                        >
                          Salva bozza
                        </button>

                        {/* Send only from draft status — forward-only, never automatic */}
                        {selected.status === "draft" && (
                          <button
                            type="button"
                            onClick={handleSend}
                            disabled={saving}
                            className="rounded-md bg-sky-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 hover:bg-sky-700"
                          >
                            Approva e invia
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {actionError && (
                    <p className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                      {actionError}
                    </p>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
