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

## OPERATING MODE (operator directive 2026-11-19 ~19:30): SEQUENTIAL agents only, minimize RAM

Host has 7.5GB RAM; parallel agents + node + docker sidecars triggered OOM SIGTERMs
(three mass-crashes). Rules now: ONE child agent at a time; no parallel docker runs;
children must kill dev servers after use and never load NLP models (inference done,
predictions on disk in WP9 worktree). Child model fallback (operator-approved):
openrouter/anthropic/claude-sonnet-4.6 (session model qwen4-max hit provider 429 quota).
Resume keeps the OLD model — to switch model, launch a FRESH child with checkpoint brief.

## STATE ~19:30

- Merged: #11/#12/#9/#10/#13/#14/#16/#15/#17 (P0) + #18 WP7 auth (c532e22) + #20 WP12
  demand memo (625aefd) + #21 WP8 11/11 ops (fd668bf). **v1.0.0 RE-TAGGED on fd668bf**
  (WP8a corrected reviews/summary examples pre-freeze). Merged-master suite green:
  backend 140+1skip, data 38, frontend 13+tsc+build, mirror, lint.
- WP9 fix pass COMMITTED+PUSHED f45776e (runner died before report; orchestrator verified:
  probe_precisions in metrics JSON, runtime labels fixed, annotations CSV committed,
  correlations unchanged 0.5517/0.5894, 23 tests, lint). Focused re-review running
  (run 4d802f9d, fallback model). On APPROVE → merge #19.
- WP10/WP11 children died at startup (OOM) — NO work done. WP10 worktree exists
  (pi-worktree-80e632a5-…-s0-0, clean @ fd668bf, auto-named branch — rename or reuse).
  WP11 not started. RUN THEM SEQUENTIALLY after #19 merges: WP10 first (worktree child),
  then WP11 (main checkout child). Briefs: see session history 2026-11-19 ~19:00
  (WP10: classifier fallback + drafts status=draft + anti-leakage test evolution to
  post-D15 semantics; WP11: reputation/search/inbox tabs, 2012-only label, HITL, 403-aware).
- WP12 worktree still on disk (merged; .venv untracked — leave or force-remove).

## IN FLIGHT (legacy ids below superseded by STATE above)

Recovery pattern that works: inspect on-disk state (worktrees survive), resume if handoff
record exists, else fresh worker with cwd=worktree + checkpoint brief. WP9 inference
COMPLETED before the crash (1638/1638 predictions + metrics + summaries JSONs on disk).

0. **WP7 MERGED** (`c532e22`, PR #18): real JWT, 49+1skip. GitGuardian gate cleared via
   orchestrator-approved squash rewrite (demo-password literal never enters master history);
   tree identity proven (978b3bc5…); hash map 2bfee0d+86edd28+6288d9d → 5626e7f.
1. **WP8 builder** run `e9c30ea3-f9f3-4437-818e-b815eb7fd01a` (resume of d43f92b6; MAIN checkout,
   branch fix/wp8-remaining-ops). 7 ops + hand-rolled contract tests + frontend CI job +
   post-seed API-tests step. **WP8a scope addition (orchestrator decision)**: reviews/summary
   pinned dimension examples were HAND-WRITTEN and match no corpus statistic (builder verified
   1638×6 row-by-row) → SECOND commit corrects examples pre-freeze to executed SQL averages
   (p1 762/3.86/4.11/3.43/4.62/3.78/4.17; p2 876/4.40/4.63/4.27/4.47/4.28/4.16), mock sync,
   tests pin all 7 + weighted both. **RE-TAG OBLIGATION: v1.0.0 must be deleted and re-applied
   on the final merged master after WP8 (spec changed pre-freeze; client hasn't seen the tag).**
2. **WP9 builder** run `d6bf5d96-5991-4e38-b962-42684f467978` (resume; WORKTREE
   pi-worktree-38ccb643-…-s0-0, branch fix/wp9-review-nlp). Inference DONE on disk; remaining:
   report docs/analysis/reputation-nlp.md, unit tests, acceptance, commit, PR. Predictions CSV
   local-only (.gitignore), metrics+summaries committed.
3. **WP12 builder** run `13aea2f2-72df-4597-89ef-eeecb0f981cd` (fresh worker, cwd = WORKTREE
   pi-worktree-c67153d1-…-s0-0, branch fix/wp12-demand-analysis; replaces crashed c67153d1).
   analyze_demand.py + demand_analysis.json exist; remaining: report, tests, acceptance, PR.

## QUEUE (deadline order; briefs were given verbally — recreate from audit + prompt)

- **WP8** (L1, after WP7 merge): remaining 7 operations (channels, seasonality, reviews/summary,
  reviews, bookings, guest-requests GET+PATCH with 403 matrix + HITL status new→draft→sent),
  contract tests in CI (pick schemathesis vs hand-rolled, justify), **frontend CI job** (missing!),
  fix CI ordering gap (schema-tests run BEFORE seed → sample-baseline API test never runs in CI).
  Reviewer ground truth precomputed: channels Online TA 33040/111540/€12973686.94 etc.;
  seasonality month-of-year (see session 2026-11-19 ~14:20 SQL; recompute if lost).
  Channels example is ILLUSTRATIVE (totals pinned, per-segment not); share = bookings fraction.
- **WP10** (L3, AFTER WP8 merge — writes guest_requests, would break WP8 zero-mutation end-state): email classifier fallback (templates/keywords, 6 categories, macro-F1 + confusion
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