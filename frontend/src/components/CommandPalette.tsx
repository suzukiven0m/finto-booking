import { useEffect, useState } from "react";
import { IconCommand, IconDashboard, IconInbox, IconLake, IconMountain, IconSearch, IconSparkles, IconX } from "./Icons";

export type AppTab = "dashboard" | "reputazione" | "ricerca" | "inbox";

export interface PaletteAction {
  id: string;
  label: string;
  hint: string;
  group: "Navigazione" | "Proprietà" | "Azioni rapide";
  run: () => void;
}

export function CommandPalette({
  open,
  onClose,
  onNavigate,
  onSelectProperty,
  onOpenDisclosures,
}: {
  open: boolean;
  onClose: () => void;
  onNavigate: (tab: AppTab) => void;
  onSelectProperty: (propertyId: string) => void;
  onOpenDisclosures: () => void;
}) {
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (open) setQuery("");
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const actions: PaletteAction[] = [
    {
      id: "nav-dashboard",
      label: "Vai a Command Center (Dashboard KPI)",
      hint: "Occupazione, RevPAR, stagionalità, canali & simulatore",
      group: "Navigazione",
      run: () => onNavigate("dashboard"),
    },
    {
      id: "nav-reputazione",
      label: "Vai a Reputazione AI & Recensioni",
      hint: "Radar 5 dimensioni, analisi NLP 2012 ed explorer",
      group: "Navigazione",
      run: () => onNavigate("reputazione"),
    },
    {
      id: "nav-ricerca",
      label: "Vai a Booking Intelligence (Ricerca)",
      hint: "Filtri segmenti, analisi rischio lead-time, export CSV",
      group: "Navigazione",
      run: () => onNavigate("ricerca"),
    },
    {
      id: "nav-inbox",
      label: "Vai a Smart Inbox (Assistente HITL)",
      hint: "Classificazione richieste e bozze con approvazione umana",
      group: "Navigazione",
      run: () => onNavigate("inbox"),
    },
    {
      id: "prop-all",
      label: "Mostra entrambe le proprietà",
      hint: "Capacità combinata assunta: 420 camere",
      group: "Proprietà",
      run: () => onSelectProperty(""),
    },
    {
      id: "prop-lago",
      label: "Filtra su Buby Lago",
      hint: "Resort Hotel · 190 camere assunte",
      group: "Proprietà",
      run: () => onSelectProperty("1"),
    },
    {
      id: "prop-montagna",
      label: "Filtra su Buby Montagna",
      hint: "City Hotel · 230 camere assunte",
      group: "Proprietà",
      run: () => onSelectProperty("2"),
    },
    {
      id: "act-disclosures",
      label: "Apri Note Metodologiche e Disclosure (v1)",
      hint: "Capacità assunta, S4 zero overlap, email sintetiche",
      group: "Azioni rapide",
      run: onOpenDisclosures,
    },
  ];

  const q = query.trim().toLowerCase();
  const filtered = q
    ? actions.filter(
        (a) =>
          a.label.toLowerCase().includes(q) ||
          a.hint.toLowerCase().includes(q) ||
          a.group.toLowerCase().includes(q),
      )
    : actions;

  function pickIcon(id: string) {
    if (id.includes("dashboard")) return <IconDashboard size={16} />;
    if (id.includes("reputazione")) return <IconSparkles size={16} />;
    if (id.includes("ricerca")) return <IconSearch size={16} />;
    if (id.includes("inbox")) return <IconInbox size={16} />;
    if (id.includes("lago")) return <IconLake size={16} className="text-teal-600" />;
    if (id.includes("montagna")) return <IconMountain size={16} className="text-amber-600" />;
    return <IconCommand size={16} />;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-slate-950/50 px-4 pt-20 backdrop-blur-xs"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Command Palette"
    >
      <div
        className="animate-enter w-full max-w-lg overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3">
          <IconSearch size={18} className="text-slate-400" />
          <input
            autoFocus
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Cerca scheda, struttura o azione rapida…"
            className="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
          />
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <IconX size={16} />
          </button>
        </div>

        <div className="max-h-80 overflow-y-auto p-2">
          {filtered.length === 0 ? (
            <p className="py-8 text-center text-xs text-slate-400">
              Nessun comando corrispondente a "{query}"
            </p>
          ) : (
            filtered.map((action) => (
              <button
                key={action.id}
                type="button"
                onClick={() => {
                  action.run();
                  onClose();
                }}
                className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors hover:bg-slate-100"
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                  {pickIcon(action.id)}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-900">{action.label}</p>
                  <p className="truncate text-xs text-slate-500">{action.hint}</p>
                </div>
                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                  {action.group}
                </span>
              </button>
            ))
          )}
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50 px-4 py-2 text-[11px] text-slate-400">
          <span>Navigazione rapida Buby Travel</span>
          <span>ESC per chiudere</span>
        </div>
      </div>
    </div>
  );
}
