import { useEffect, useState } from "react";

import { SESSION_EXPIRED } from "./api/client";
import App from "./App";
import Login from "./Login";
import { clearSession, loadSession, saveSession } from "./session";
import type { Session } from "./session";

// il "portiere": se non sei entrato vedi il login, altrimenti la dashboard
export default function AuthGate() {
  const [session, setSession] = useState<Session | null>(loadSession);

  function logout() {
    clearSession();
    setSession(null);
  }

  // se l'api risponde 401 (token scaduto) si torna al login
  useEffect(() => {
    window.addEventListener(SESSION_EXPIRED, logout);
    return () => window.removeEventListener(SESSION_EXPIRED, logout);
  }, []);

  if (!session) {
    return (
      <Login
        onLogin={(next) => {
          saveSession(next);
          setSession(next);
        }}
      />
    );
  }
  return <App session={session} onLogout={logout} />;
}
