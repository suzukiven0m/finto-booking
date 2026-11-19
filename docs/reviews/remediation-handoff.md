# Remediation handoff — 2026-11-19 ~17:10 CET (orchestrator session pause)

Resume point for the shepherd remediation workflow (prompt: builder → independent
reviewer → fix → merge; audit backlog `2026-11-19-shepherd-audit.md`).

## DONE — P0 complete, freeze package ready (SAL 1 tomorrow Fri 2026-11-20)

- **Tag `v1.0.0` pushed** on master `74690c5` (schema 0001–0005 + contract 1.0.0).
- Merged PRs today: #11 WP1 contract S1/S2/S3 (`9e3f37c`) · #12 WP2 S7/S8+0005 (`cc732bf`) ·
  #9 KPI API (`dc572e0`) · #10 login UI (`1fb7527`) · #13 WP6 ledger (`cf0a53a`) ·
  #14 WP4 doc corrections (`39cf1f1`) · #16 WP2b NLP-wording consistency (`d60870c`) ·
  #15 WP5 SAL package (`0e62b0b`) · #17 WP7a role matrix (`74690c5`).
- WP3 = merge of #9/#10 with recorded gaps G1–G5 (auth→WP7, ops→WP8, mock-default→WP13).
- Audit §7 matrix row closed as **AUDIT-IN-ERROR** (printed ADR totals correct by execution).
- Operator decision 2026-11-19: role matrix = all roles read; guest-requests PATCH admin/manager;
  property_manager → 403. Frozen in spec (WP7a).
- Records committed: wp1, wp2, wp3, wp6. **Records drafted in /tmp, NOT yet committed**:
  `/tmp/wp4-record.md`, `/tmp/wp2b-record.md`, `/tmp/wp5-record.md`, `/tmp/wp7a-record.md`
  → commit as `docs/reviews/2026-11-19-wp{4,2b,5,7a}.md` via the next docs PR.
- Live DB `buby` at 0005, seeded, baseline exact (61777/218410/€22976960.13/105.20/0.2749).
- Tagged-master suite green: backend 28+1skip, data 12, frontend 3+tsc+build, lint, mirror.

## IN FLIGHT (updated after runner crash ~17:12 and recovery ~17:40)

Both original runners died while the operator was away (stale-run reconciliation).
Recovery: WP7 reviewer RESUMED (context preserved); WP9 resume had no handoff record
(children: []) → fresh worker launched IN THE SAME WORKTREE with a checkpoint brief
(partial code survives uncommitted; crash-resilient nohup+incremental-checkpoint pattern mandated).

1. **WP7 reviewer** run `0473b42b-6f17-43d9-b6d5-2e90000759c5` (resume of da18f6ea; agent reviewer, read-only, no shell).
   Object: PR **#18** `fix/wp7-real-auth` @ `86edd28` (real JWT, 48+1skip backend, 13 frontend).
   Orchestrator execution gate ALREADY GREEN (tampered/expired/alg-none/wrong-creds → 401;
   baseline unchanged; data 12 with raw mount; lint clean). On APPROVE: sign-off comment +
   `gh pr merge 18 --admin --merge` (protocol below), then launch WP8.
   Artifact: ~/.pi/agent/sessions/--home-suzuki-code-finto-booking--/subagent-artifacts/da18f6ea-*_reviewer_output.md
2. **WP9 builder** run `cefbefa1-4e20-4cc2-80ce-d69c505806b9` (fresh worker, cwd = WORKTREE
   /home/suzuki/code/worktrees/finto-booking/pi-worktree-38ccb643-7497-4acb-b814-b8ad113787fb-s0-0, branch fix/wp9-review-nlp; replaces crashed 38ccb643).
   D14 review NLP: torch 2.9.1+cpu / transformers 4.57.6 installed in worktree .venv;
   models cached+pinned (cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual @82107f4,
   facebook/bart-large-mnli @d7645e1); was calibrating zero-shot thresholds then full 1,638-body run.
   On completion: extract branch, independent review (eval re-run!), merge via PR.
   Check: `subagent({action:"status",id:"cefbefa1",options:{view:"transcript",index:0}})`.

## QUEUE (deadline order; briefs were given verbally — recreate from audit + prompt)

- **WP8** (L1, after WP7 merge): remaining 7 operations (channels, seasonality, reviews/summary,
  reviews, bookings, guest-requests GET+PATCH with 403 matrix + HITL status new→draft→sent),
  contract tests in CI (pick schemathesis vs hand-rolled, justify), **frontend CI job** (missing!),
  fix CI ordering gap (schema-tests run BEFORE seed → sample-baseline API test never runs in CI).
  Reviewer ground truth precomputed: channels Online TA 33040/111540/€12973686.94 etc.;
  seasonality month-of-year (see session 2026-11-19 ~14:20 SQL; recompute if lost).
  Channels example is ILLUSTRATIVE (totals pinned, per-segment not); share = bookings fraction.
- **WP10** (L3): email classifier fallback (templates/keywords, 6 categories, macro-F1 + confusion
  matrix vs data/eval/email_gold.csv, NEVER in DB), draft replies status=draft never auto-sent;
  LLM upgrade **blocked on O2 keys (human, overdue)**. Gold alignment: same-run TRUNCATE RESTART IDENTITY.
- **WP11** (L2, after WP8): reputation page (real scores per frozen ReviewSummary; trend labeled
  2012-only), bookings search, inbox HITL; vitest for new API paths; Prism AND real API.
- **WP12** (L3): demand/pricing analysis memo (every number recomputable by cited query);
  D16 forecast stretch-or-waiver → HA-14.
- **WP13** (P2): VITE_API_BASE_URL default → real API, E2E in CI, zero Prism in demo path.
- **WP14** (P3): compose api/web + Dockerfiles, deploy decision (accounts human-gated HA-10),
  install docs, demo script ≤10min rehearsed ×2, final report.
- **Final**: docs/reviews/2026-11-19-remediation-status.md — every S/R/§7/§8 item →
  closed/open/blocked/human-gated + phase scorecard + ledger summary. Commit records above with it.

## PROTOCOLS / TRAPS (do not rediscover)

- **Merge gate**: CI green (`gh pr checks N`) + independent sign-off posted as PR comment +
  `gh pr merge N --admin --merge --delete-branch=false` (single gh account = author → self-approval
  blocked; protection enforce_admins=false; HA-13 tracks second-account need). Never direct code to master.
- **Reviewer agent has NO shell** — static review + PENDING-EXECUTION commands; orchestrator executes
  and labels evidence as orchestrator-run (house pattern, plumbing-review.md).
- **Host→container TCP BLOCKED (VPN)**: all DB work via sidecar:
  `docker run --rm -i --network container:buby-postgres -v "$PWD":/repo:ro -w /repo/backend
  -e PYTHONPATH=/repo/backend/.venv/lib/python3.12/site-packages:/repo/backend
  -e PYTEST_ADDOPTS="-p no:cacheprovider" python:3.12-slim sh -c "python -m alembic check && python -m pytest -q"`
  (data tests: -w /repo, pytest data/tests, PYTHONPATH +=:/repo/data; full CSV gitignored → mount
  -v $PWD/data/raw:/repo/data/raw:ro for 12 passed; extractions need -v mainrepo:/host:ro for the venv).
- Scratch DBs only for downgrade tests (CREATE/DROP via psycopg autocommit on 'buby'; raw psycopg
  URL = postgresql:// not postgresql+psycopg://). NEVER downgrade seeded buby.
- venv has no pip → `uv pip install --python backend/.venv/bin/python …` (uv at ~/.local/bin/uv).
- Baseline is an assertion: 87396 rows / 61777 valid / 218410 rn / €22976960.13 / 105.20 / 0.2749;
  sample 5000/3564/12696/€1350503.84/0.2696. Never adjust to make green.
- Anti-leakage: true_category/true_urgency only in data/eval/email_gold.csv; guest_requests
  category/draft_reply/urgency NULL until D15. Mock sync: cp openapi.yaml frontend/mock/openapi.yaml
  same commit; diff -q clean; redocly 0 errors. Post-freeze contract changes = bump protocol
  (ADR + info.version + migration + mock + client note in docs/client-comms.md).
- Humans owe (docs/reviews/human-actions.md, never agent-closed): HA-01 KPI sign-off, HA-02 O5 send
  (text ready docs/sal1/o5-status.md), HA-03 solo notification, HA-04 reassignment (D14 owner first),
  HA-05 O2 keys (OVERDUE, blocks WP10 LLM), HA-06/07/08/09 O1/O3/O4/B4, HA-10 deploy accounts,
  HA-11 SAL1 present, HA-12 demo+rehearsals, HA-13 second gh account, HA-14 §11 contradictions
  (auth half resolved by WP7 implementation; forecast half → WP12 memo at SAL 1).