import { useState } from "react";
import type { FormEvent } from "react";

import { ApiError, login } from "./api/client";
import type { Session } from "./session";

// login vero (D11/WP7): chiama POST /api/auth/login, che valida le credenziali
// sugli utenti demo e emette un JWT con il ruolo. Gli errori 401 li mostra il form.
export default function Login({ onLogin }: { onLogin: (session: Session) => void }) {
  const [email, setEmail] = useState("manager@buby.travel");
  const [password, setPassword] = useState("");
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
        setError("Wrong email or password.");
      } else if (err instanceof ApiError) {
        setError(`${err.message} (${err.code})`);
      } else {
        setError("Could not reach the API. Is the backend or the mock running?");
      }
      setLoading(false);
    }
  }

  const inputClass =
    "mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 text-slate-900">
      <form
        onSubmit={submit}
        className="w-full max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div>
          <h1 className="text-xl font-semibold">Buby Travel — Dashboard</h1>
          <p className="text-sm text-slate-500">Sign in to see the KPIs</p>
        </div>

        <label className="block text-xs font-medium text-slate-500">
          Email
          <input
            type="email"
            required
            autoComplete="username"
            className={inputClass}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label className="block text-xs font-medium text-slate-500">
          Password
          <input
            type="password"
            required
            autoComplete="current-password"
            className={inputClass}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>

        {error && (
          <p
            role="alert"
            className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          >
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>

        <p className="text-xs text-slate-400">
          Demo users (published dev defaults, not secrets): admin@buby.travel,
          manager@buby.travel, property.manager@buby.travel — password: demo.
        </p>
      </form>
    </div>
  );
}
