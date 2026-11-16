import { setToken } from "./api/client";

// chi e' entrato: serve per mostrare email e ruolo e per il logout
export interface Session {
  email: string;
  role: string;
  token: string;
}

const KEY = "buby-session";

export const ROLE_LABELS: Record<string, string> = {
  admin: "Admin",
  manager: "Manager",
  property_manager: "Property manager",
};

// sessionStorage: resta se ricarichi la pagina, sparisce quando chiudi la scheda
export function loadSession(): Session | null {
  try {
    const saved = sessionStorage.getItem(KEY);
    if (!saved) return null;
    const session = JSON.parse(saved) as Session;
    setToken(session.token);
    return session;
  } catch {
    return null;
  }
}

export function saveSession(session: Session) {
  setToken(session.token);
  try {
    sessionStorage.setItem(KEY, JSON.stringify(session));
  } catch {
    // se il browser blocca lo storage si resta dentro solo fino alla ricarica
  }
}

export function clearSession() {
  setToken(null);
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    // niente da fare
  }
}
