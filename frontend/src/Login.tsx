import { useState } from "react";
import type { FormEvent } from "react";

import { ApiError, login } from "./api/client";
import { IconLake, IconMountain, IconShield, IconSparkles } from "./components/Icons";
import type { Session } from "./session";

const DEMO_ACCOUNTS = [
  {
    email: "admin@buby.travel",
    role: "Admin",
    permissions: "Accesso completo · Lettura + Approvazione Inbox",
    accent: "border-slate-300 bg-slate-900 text-white",
  },
  {
    email: "manager@buby.travel",
    role: "Manager",
    permissions: "Direzione · KPI + Modifica & Invio bozze HITL",
    accent: "border-teal-200 bg-teal-50/70 text-teal-950",
  },
  {
    email: "property.manager@buby.travel",
    role: "Property Manager",
    permissions: "Sola lettura · 403 su invio/modifica Inbox",
    accent: "border-amber-200 bg-amber-50/70 text-amber-950",
  },
];

export default function Login({ onLogin }: { onLogin: (session: Session) => void }) {
  const [email, setEmail] = useState("manager@buby.travel");
  const [password, setPassword] = useState("demo");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await login(email, password);
      onLogin({ email, role: result.role, token: result.access_token });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Email o password non corretti.");
      } else if (err instanceof ApiError) {
        setError(`${err.message} (${err.code})`);
      } else {
        setError("Impossibile raggiungere l'API. Verifica che il backend (:8000) o il mock (:4010) siano attivi.");
      }
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen bg-[#F6F5F1] text-slate-900 lg:grid-cols-12">
      {/* Left editorial panel */}
      <section className="relative flex flex-col justify-between overflow-hidden bg-slate-950 p-8 text-white lg:col-span-7 lg:p-12">
        <div
          className="pointer-events-none absolute inset-0 opacity-30"
          style={{
            background:
              "radial-gradient(circle at 15% 20%, rgba(20,184,166,0.45), transparent 45%), radial-gradient(circle at 85% 80%, rgba(245,158,11,0.35), transparent 45%)",
          }}
        />

        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-teal-200 backdrop-blur-xs">
            <IconSparkles size={14} />
            <span>Buby Group · Caso 1 Turismo</span>
          </div>
          <h1 className="mt-6 max-w-xl text-3xl font-extrabold tracking-tight text-white sm:text-4xl lg:text-5xl">
            Buby Travel{" "}
            <span className="bg-gradient-to-r from-teal-300 to-amber-300 bg-clip-text text-transparent">
              Hospitality Intelligence
            </span>
          </h1>
          <p className="mt-4 max-w-lg text-sm leading-relaxed text-slate-300 sm:text-base">
            Control room unificata per direzione e property management: KPI di occupazione e ricavi,
            analisi reputazionale NLP, esplorazione prenotazioni e assistente email human-in-the-loop.
          </p>
        </div>

        {/* Property cards */}
        <div className="relative z-10 my-8 grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xs">
            <div className="flex items-center gap-2.5 text-teal-300">
              <IconLake size={20} />
              <span className="text-xs font-semibold uppercase tracking-wider">Struttura 1</span>
            </div>
            <h2 className="mt-2 text-lg font-bold text-white">Buby Lago</h2>
            <p className="mt-1 text-xs text-slate-300">
              Resort Hotel · <strong>190 camere</strong> (capacità assunta) · Forte stagionalità estiva
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xs">
            <div className="flex items-center gap-2.5 text-amber-300">
              <IconMountain size={20} />
              <span className="text-xs font-semibold uppercase tracking-wider">Struttura 2</span>
            </div>
            <h2 className="mt-2 text-lg font-bold text-white">Buby Montagna</h2>
            <p className="mt-1 text-xs text-slate-300">
              City Hotel · <strong>230 camere</strong> (capacità assunta) · Domanda bilanciata annuale
            </p>
          </div>
        </div>

        <div className="relative z-10 flex flex-wrap items-center gap-4 text-xs text-slate-400">
          <span className="inline-flex items-center gap-1.5">
            <IconShield size={14} className="text-teal-400" />
            Contratto OpenAPI v1.0.0 congelato
          </span>
          <span>·</span>
          <span>Autenticazione JWT Bearer (HS256)</span>
          <span>·</span>
          <span>S4 & Disclosure vincolanti attive</span>
        </div>
      </section>

      {/* Right auth panel */}
      <section className="flex items-center justify-center p-6 sm:p-10 lg:col-span-5">
        <div className="animate-enter w-full max-w-md space-y-6">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">Accedi alla piattaforma</h2>
            <p className="mt-1 text-sm text-slate-500">
              Seleziona un profilo demo o inserisci le credenziali aziendali.
            </p>
          </div>

          {/* Quick role switcher */}
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Profili Demo (password: <code className="font-mono text-slate-700">demo</code>)
            </p>
            <div className="grid gap-2">
              {DEMO_ACCOUNTS.map((acc) => {
                const active = email === acc.email;
                return (
                  <button
                    key={acc.email}
                    type="button"
                    onClick={() => {
                      setEmail(acc.email);
                      setPassword("demo");
                      setError(null);
                    }}
                    className={`flex items-center justify-between rounded-xl border px-3.5 py-2.5 text-left transition-all ${
                      active
                        ? "border-teal-600 bg-white ring-2 ring-teal-600/20 shadow-sm"
                        : "border-slate-200 bg-white/80 hover:border-slate-300 hover:bg-white"
                    }`}
                  >
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{acc.role}</p>
                      <p className="text-xs text-slate-500">{acc.permissions}</p>
                    </div>
                    <span className="font-mono text-[11px] text-slate-400">{acc.email.split("@")[0]}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <form
            onSubmit={submit}
            className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Email
              <input
                type="email"
                required
                autoComplete="username"
                className="mt-1.5 w-full rounded-xl border border-slate-300 bg-slate-50/50 px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-teal-600 focus:bg-white focus:ring-2 focus:ring-teal-600/15"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>

            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Password
              <input
                type="password"
                required
                autoComplete="current-password"
                className="mt-1.5 w-full rounded-xl border border-slate-300 bg-slate-50/50 px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-teal-600 focus:bg-white focus:ring-2 focus:ring-teal-600/15"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>

            {error && (
              <p
                role="alert"
                className="rounded-xl border border-red-200 bg-red-50 px-3.5 py-2.5 text-xs font-medium text-red-700"
              >
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:opacity-50"
            >
              {loading ? "Verifica credenziali JWT…" : "Entra nella Control Room"}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
