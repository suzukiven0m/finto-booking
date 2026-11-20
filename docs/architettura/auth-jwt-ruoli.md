# Autenticazione: gettone JWT e matrice dei ruoli

## Cos'è

L'autenticazione risponde a due domande: "chi sei?" e "cosa puoi fare?".
Noi usiamo un gettone JWT (JSON Web Token): una stringa firmata che il server
rilascia al login e che il client rimanda a ogni chiamata protetta. Dentro ci
sono l'identità (email), il ruolo e una scadenza. Il server la verifica senza
dover ricordare nulla in memoria: la firma dimostra che l'ha emessa lui.

## Perché l'abbiamo disegnato così

Il brief nomina esplicitamente l'autenticazione tra le attività WSA, e
[ADR 0001](../adr/0001-tech-stack.md) fissa JWT con tre ruoli: `admin`,
`manager`, `property_manager`.

La decisione più importante è registrata come S7 (pre-freeze): **niente
tabella utenti nello schema v1**. Gli utenti demo sono hardcoded in
`backend/app/config.py`. Perché? Lo schema si congelava al SAL 1: aggiungere
una tabella utenti dopo il freeze avrebbe richiesto un contract-bump davanti
al cliente. Una tabella vera più avanti è possibile, ma segue la procedura
scritta (nuova ADR, bump di versione, migrazione dedicata). Per una demo
laboratorio tre utenti fissi bastano e non costano una migrazione.

La matrice dei ruoli è stata decisa dall'operatore il 19 novembre 2026
(WP7a), perché il contratto dichiarava un 403 solo sulla PATCH delle richieste
ospiti ma non diceva quali ruoli potessero scrivere. La regola scelta:

- Tutti e tre i ruoli leggono ogni GET protetta (nessuno scoping per proprietà
  in v1).
- La PATCH su `/api/guest-requests/{id}` richiede `admin` o `manager`.
- `property_manager` riceve il 403 previsto dal contratto.

Abbiamo scartato i cookie di sessione (stato sul server, più infrastruttura),
OAuth (sovradimensionato per un lab) e una tabella utenti subito (violazione
del freeze).

Sicurezza del gettone: algoritmo HS256 fissato (niente "alg=none", attacco
testato e respinto con 401), scadenza 8 ore obbligatoria, firma sempre
verificata, claim `exp/sub/role` richiesti. Le credenziali si confrontano con
`secrets.compare_digest` (tempo costante, niente timing attack) e utente
inesistente o password sbagliata danno lo stesso 401 identico (niente
enumerazione utenti). Un ruolo non-stringa nel gettone dà 403, non un 500.

I default pubblicati (password `demo`, segreto JWT di sviluppo) NON sono
segreti: sono scritti in `docs/api-contract.md` perché la demo funzioni senza
configurazione. Un deploy reale DEVE impostare `POSTGRES_PASSWORD` e
`JWT_SECRET` via variabili d'ambiente. Questo è il posture S7, dichiarato.

## Com'è fatto in pratica

- `backend/app/config.py`: `DEMO_USERS` (tre utenti, un ruolo ciascuno),
  `JWT_SECRET` da env con default di sviluppo, algoritmo e scadenza.
- `backend/app/auth.py`: login (valida credenziali, emette JWT), dipendenza
  `get_current_user` (verifica il gettone), `require_write_role` (matrice).
- PyJWT==2.10.1, versione fissata: la crittografia è un confine di fiducia,
  non si scrive a mano.
- Le rotte aperte (`/api/properties`, `/api/auth/login`) hanno `security: []`
  nel contratto; tutte le altre richiedono il gettone.

## Limiti e cosa può andare storto

- Tre utenti hardcoded non sono un sistema di identity management: niente
  registrazione, niente reset password, niente revoca individuale del gettone
  (scade da solo dopo 8 ore). Per il lab va bene; per un prodotto reale serve
  la tabella utenti e il contract-bump.
- Il segreto di sviluppo è pubblico: chiunque può firmare gettoni validi in
  locale. È voluto per la demo, ma in produzione il segreto va cambiato e
  tenuto fuori dal repo.
- La matrice non fa scoping per proprietà: un `property_manager` legge i dati
  di entrambe le strutture. Se servisse isolamento per proprietà, sarebbe una
  modifica di contratto (bump), non un cambio silenzioso.

## Riferimenti

- [ADR 0001: stack](../adr/0001-tech-stack.md)
- [Contratto API: auth e matrice](../api-contract.md)
- [Dizionario dati: decisioni pre-freeze S7/S8](../data-dictionary.md)
- [Processo e governance](processo-governance.md)
- Codice: `backend/app/config.py`, `backend/app/auth.py`
