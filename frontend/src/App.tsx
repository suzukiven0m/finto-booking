import { useEffect, useState } from "react";
import { getProperties } from "./api/client";
import type { Property } from "./api/types";
import { CommandPalette } from "./components/CommandPalette";
import type { AppTab } from "./components/CommandPalette";
import { DisclosuresModal } from "./components/DisclosuresModal";
import {
  IconCommand,
  IconDashboard,
  IconInbox,
  IconInfo,
  IconLogOut,
  IconSearch,
  IconSparkles,
} from "./components/Icons";
import Dashboard from "./pages/Dashboard";
import Inbox from "./pages/Inbox";
import Reputazione from "./pages/Reputazione";
import Ricerca from "./pages/Ricerca";
import { ROLE_LABELS } from "./session";
import type { Session } from "./session";

const TABS: Array<{ id: AppTab; label: string; subtitle: string }> = [
  { id: "dashboard", label: "Command Center", subtitle: "KPI, stagionalità, canali & simulatore" },
  { id: "reputazione", label: "Reputazione AI", subtitle: "Radar 5 dimensioni, NLP 2012 & explorer" },
  { id: "ricerca", label: "Booking Intelligence", subtitle: "Ricerca avanzata, lead-time & CSV" },
  { id: "inbox", label: "Smart Inbox HITL", subtitle: "Triage richieste & bozze con approvazione" },
];

export default function App({ session, onLogout }: { session: Session; onLogout: () => void }) {
  const [tab, setTab] = useState<AppTab>("dashboard");
  const [properties, setProperties] = useState<Property[]>([]);
  const [propertyId, setPropertyId] = useState("");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [disclosuresOpen, setDisclosuresOpen] = useState(false);

  useEffect(() => {
    getProperties()
      .then(setProperties)
      .catch(() => {
        // Fallback properties handled in child components
      });
  }, []);

  // Global Ctrl+K / Cmd+K shortcut for Command Palette
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  function tabIcon(id: AppTab) {
    if (id === "dashboard") return <IconDashboard size={16} />;
    if (id === "reputazione") return <IconSparkles size={16} />;
    if (id === "ricerca") return <IconSearch size={16} />;
    return <IconInbox size={16} />;
  }

  const activeTabMeta = TABS.find((t) => t.id === tab)!;

  return (
    <div className="flex min-h-screen flex-col bg-[#F6F5F1] text-slate-900">
      {/* Top sticky glass header */}
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3.5 sm:px-6">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-teal-400 shadow-xs">
              <IconSparkles size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-extrabold tracking-tight text-slate-950 sm:text-lg">
                  Buby Travel
                </h1>
                <span className="rounded-full bg-teal-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-teal-700">
                  v1.0.0
                </span>
              </div>
              <p className="text-xs text-slate-500">
                {activeTabMeta.label} · {activeTabMeta.subtitle}
              </p>
            </div>
          </div>

          {/* Right controls: Command Palette, Disclosures, Session + Logout */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setPaletteOpen(true)}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-white"
            >
              <IconCommand size={14} className="text-slate-400" />
              <span className="hidden sm:inline">Comando rapido</span>
              <kbd className="rounded border border-slate-200 bg-white px-1.5 py-0.5 font-mono text-[10px] text-slate-500">
                Ctrl K
              </kbd>
            </button>

            <button
              type="button"
              onClick={() => setDisclosuresOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50"
            >
              <IconInfo size={14} className="text-teal-600" />
              <span className="hidden md:inline">Limiti & Disclosure</span>
            </button>

            <div className="hidden h-5 w-px bg-slate-200 sm:block" />

            <div className="flex items-center gap-2 rounded-xl border border-slate-200/80 bg-slate-50/70 px-3 py-1.5 text-xs">
              <span className="max-w-[140px] truncate font-medium text-slate-700">
                {session.email}
              </span>
              <span className="rounded-full bg-slate-900 px-2 py-0.5 text-[10px] font-semibold text-white">
                {ROLE_LABELS[session.role] ?? session.role}
              </span>
            </div>

            <button
              type="button"
              onClick={onLogout}
              title="Esci"
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200"
            >
              <IconLogOut size={14} />
              <span className="hidden sm:inline">Esci</span>
            </button>
          </div>
        </div>

        {/* Navigation tabs */}
        <nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 pb-2 sm:px-6" aria-label="Sezioni">
          {TABS.map((t) => {
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={`inline-flex shrink-0 items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition ${
                  active
                    ? "bg-slate-950 text-white shadow-xs"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                }`}
              >
                {tabIcon(t.id)}
                <span>{t.label}</span>
              </button>
            );
          })}
        </nav>
      </header>

      {/* Main Content */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">
        {tab === "dashboard" && (
          <Dashboard
            properties={properties}
            propertyId={propertyId}
            onChangePropertyId={setPropertyId}
          />
        )}

        {tab === "reputazione" && (
          <Reputazione propertyId={propertyId} onChangePropertyId={setPropertyId} />
        )}

        {tab === "ricerca" && (
          <Ricerca propertyId={propertyId} onChangePropertyId={setPropertyId} />
        )}

        {tab === "inbox" && (
          <Inbox
            session={session}
            propertyId={propertyId}
            onChangePropertyId={setPropertyId}
          />
        )}
      </main>

      {/* Disclosures footer — visible on every page (binding per openapi.yaml + docs/api-contract.md) */}
      <footer className="border-t border-slate-200/80 bg-white/70">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4 text-[11px] leading-relaxed text-slate-500 sm:px-6">
          <p>
            Occupancy &amp; RevPAR usano <strong>capacità assunta</strong> (Buby Lago 190 camere,
            Buby Montagna 230 camere), non misurata. Il legame recensioni↔prenotazioni è{" "}
            <strong>asserito</strong> a livello di proprietà (corpus 2012 vs prenotazioni
            2015–2017, zero overlap). Le email degli ospiti sono <strong>sintetiche</strong> e le
            due strutture sono fittizie.
          </p>
          <button
            type="button"
            onClick={() => setDisclosuresOpen(true)}
            className="shrink-0 font-semibold text-teal-700 hover:underline"
          >
            Dettagli contratto v1 →
          </button>
        </div>
      </footer>

      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        onNavigate={setTab}
        onSelectProperty={setPropertyId}
        onOpenDisclosures={() => setDisclosuresOpen(true)}
      />

      <DisclosuresModal
        open={disclosuresOpen}
        onClose={() => setDisclosuresOpen(false)}
      />
    </div>
  );
}
