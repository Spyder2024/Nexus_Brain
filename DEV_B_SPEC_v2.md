# NexusBrain: Dev B Build Spec v2 (Next.js on Vercel + FastAPI on Render)

Hand this whole file to the coding agent. It replaces `DEV_B_SPEC.md`. **Streamlit is gone.** Read `README.md`, `.agent/TRD.md`, `.agent/RULES.md` and `src/schema/models.py` first.

Dev B owns: `src/api/`, `frontend/`, `README.md`. Do not edit `src/schema/`, `src/data_gen/`, `src/graph/`, `src/agents/` or the `Dockerfile` (Dev A). If something there blocks you, write the need down in `HANDOFF_TO_DEV_A.md` and keep going against the mock.

Deadline: submissions close **Oct 18, 11:59 PM IST**. Deployed link plus demo video is the goal.

---

## 1. Architecture

```
Vercel   Next.js 14 (App Router, TS) + Tailwind + react-force-graph-2d
           frontend/src/lib/api.ts  (typed fetch client)
              |  HTTPS JSON, NEXT_PUBLIC_API_URL
              v
Render   Docker web service (free tier)
           FastAPI + Uvicorn  (src/api/server.py)
             -> Backend interface (src/api/backend.py)
                 LiveBackend -> AgentCoordinator / GraphTools   (Dev A)
                 MockBackend -> canned Golden Scenarios         (fallback)
             -> singleton FalkorDB client, background auto-seed
              |  Redis protocol (TLS if enabled)
              v
FalkorDB Cloud   graph `company_brain` + `memory_tenant_{user_id}`

UptimeRobot / cron-job.org  -> GET /api/v1/health every 5-10 min (anti spin-down)
```

Rules:
1. The browser never talks to FalkorDB. Only to the API.
2. No Cypher in `src/api/` or `frontend/`. The API calls tool methods; the UI renders what comes back.
3. Every API response validates against the Pydantic models. The TypeScript types mirror them 1:1.
4. Mock fallback is allowed but never silent: if the UI or API is in mock mode, show a visible "MOCK DATA" badge. The demo video and final submission must run in live mode.

---

## 2. API contract (source of truth for both sides)

Base: `NEXT_PUBLIC_API_URL`. All errors return `{"error": {"code": str, "message": str}}`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/health` | keep-alive, must answer in under a second |
| GET | `/api/v1/stats?user_id=meera` | live counts and latency |
| POST | `/api/v1/query` | ask the brain |
| POST | `/api/v1/mutate` | inject a decision (Tab 2) |
| GET | `/api/v1/memory/{user_id}` | turns and playbooks (Tab 3) |
| POST | `/api/v1/reset` | re-seed Golden Scenarios |

**health** -> `{"status":"awake","falkordb_connected":true,"seeded":true,"mode":"live","timestamp":"..."}`
Never block on the database: ping with a ~1s timeout and report `falkordb_connected:false` instead of hanging.

**stats** -> `{"mode","nodes","edges","graphs":[...],"active_tenant_graph","avg_query_ms"}`

**query** request: `{"user_id":"meera|kabir|riya","query":"...","session_id":"sess_01"}`
Response (exactly TRD Section 6): `answer`, `tenant_graph`, `agent_trace[]` (`agent`, `tool`, `cypher_executed`, `latency_ms`), `citations[]` (`id`, `label`, `title`, `status`, `source_ref`), `subgraph{nodes[],edges[]}`. Optional extra: `llm_fallback: bool`.

**mutate** request:
```json
{"user_id":"meera","source_type":"SlackThread","channel":"#arch-sync",
 "system_name":"auth-service","new_decision_title":"...",
 "supersedes_decision_id":"ADR-051","rationale":"..."}
```
The API maps this onto `GraphTools.mutate_knowledge_state(superseded_id, new_id, title, reason)`; **the server generates `new_id`** (next free ADR number, `ADR-061` on a fresh seed). Response: `{"new_decision":{...},"superseded_decision":{...,"status":"superseded"},"subgraph":{...},"latency_ms":..,"cypher_executed":".."}`. Superseding something not `active` -> 409 with a readable message.

**memory/{user_id}** -> `{"tenant_graph","turns":[...],"playbooks":[...],"shared_playbooks":[...]}`. If Dev A has no list methods yet, ask for `list_turns(user_id)` and `list_playbooks(user_id)` in `HANDOFF_TO_DEV_A.md` and serve the mock meanwhile.

**reset** -> `{"reseeded":true,"nodes":..,"edges":..}`. Idempotent. Clears tenant turns, keeps seeded playbooks.

Known inconsistencies to resolve with Dev A *before* wiring live (pick one, apply everywhere):
- Tenant id: use `memory_tenant_{user_id}` with `meera|kabir|riya` (the sample payloads disagree: `memory_tenant_meera_sre` vs `memory_tenant_meera`).
- Scenario #1 expert is **Kavya (`person-19`)** per README, not "Meera (SRE)" as in the sample subgraph. Meera is the SRE Lead persona, a different person.
- ADR-019 `source_ref`: README says `INC-204`, the sample says `DOC-004`. Follow the dataset.

---

## 3. Backend (FastAPI on Render)

### Files
```
src/api/
  server.py      app factory, routers, CORS, startup, error handlers
  backend.py     Backend Protocol + LiveBackend
  mock_bridge.py MockBackend (5 scenarios + mutable ADR state)
  schemas.py     request models + extra response models
  deps.py        mode selection, singleton backend
Dockerfile        (Dev A owns; verify it matches section 6)
```

### Behaviors
- **Config from env:** `FALKORDB_HOST`, `FALKORDB_PORT`, `FALKORDB_USERNAME`, `FALKORDB_PASSWORD`, `FALKORDB_SSL`, `GEMINI_API_KEY` (optional), `NEXUS_MODE` (`live` default, `mock` forces mock), `CORS_ORIGINS` (comma list).
- **Bind to `$PORT`** (Render injects it): `uvicorn src.api.server:app --host 0.0.0.0 --port ${PORT:-8000}`.
- **CORS:** allow origins from `CORS_ORIGINS` plus `allow_origin_regex=r"https://.*\.vercel\.app"` so preview deployments work. `http://localhost:3000` for local.
- **Singleton connection pool** created once at startup, reused by all requests.
- **Auto-seed on boot, in the background.** On startup, if `company_brain` is empty, seed it in a background thread guarded by a lock. The server must start answering `/health` immediately (Render times out slow boots). While seeding, `health.seeded=false` and `/query` returns 503 with "seeding, retry in a few seconds".
- **Mode:** if FalkorDB is unreachable at boot, fall back to mock and report `mode:"mock"` in `/health` and `/stats`.
- **Latency:** time every backend call with `time.perf_counter()`; report real numbers only. Never hardcode benchmark values.
- **Errors:** FalkorDB down -> 503 envelope, no stack traces. Unknown `user_id` or empty query -> 422.
- **Sync endpoints** (`def`) unless the client is async.
- **Reset is public** and judges share one graph. Fine for a demo, but add an optional `X-Admin-Token` check if `ADMIN_TOKEN` is set, and tell the user.
- **MockBackend mutation** must really flip ADR-051 to superseded and make the new ADR active so Preset #2 reflects it afterwards.

### Tests: `tests/test_04_api.py` (FastAPI `TestClient`, mock mode)
1. `/health` returns quickly with `mode`.
2. All 5 presets return payloads that parse as the TRD model with non-empty `agent_trace`.
3. Preset #2 cites ADR-051 `active` and ADR-019 `superseded`.
4. `/mutate` then Preset #2 shows the new ADR active and ADR-051 superseded.
5. Repeat `/mutate` on the same id -> 409.
6. `/reset` restores the original Preset #2 result.
7. `/memory/riya` has `playbook-003` in `shared_playbooks` and none of Meera's turns.
8. CORS preflight from a `*.vercel.app` origin succeeds.

---

## 4. Frontend (Next.js 14 on Vercel)

### Stack
Next.js 14 App Router, TypeScript, Tailwind CSS, `react-force-graph-2d` (load with `next/dynamic` and `ssr:false`, it needs `window`), `react-markdown` for answers. Plain React state or a tiny context, no heavy state library.

### Files
```
frontend/
  package.json  next.config.mjs  tailwind.config.ts  .env.example
  src/
    app/layout.tsx  app/page.tsx  app/globals.css
    lib/api.ts          typed client, timeouts, error mapping, optional mock fallback
    lib/types.ts        TS mirror of the contract (QueryResponse, Citation, Subgraph, ...)
    lib/presets.ts      5 preset questions + which persona each uses
    components/
      Header.tsx            persona dropdown + telemetry badge
      AskBrainTab.tsx       preset buttons, chat input, message list
      MutatorTab.tsx        injection form
      MemoryTab.tsx         turns + playbooks
      CitationBadge.tsx
      ForceGraph.tsx        graph canvas + legend
      TraceDrawer.tsx       agent_trace with Cypher + latency
      ApiStatusBanner.tsx   "waking up API", "mock data", error states
```

### Layout (README Section 7)
- **Header:** persona dropdown (Meera, Kabir, Riya) + telemetry badge from `/stats` (polled every ~15s): connection dot, `N nodes | M edges | last X ms`, red `MOCK DATA` chip when mode is mock.
- **Body:** two columns, 45% / 55% on desktop; stacked on mobile.
  - **Left:** tabs. Tab 1 Ask Company Brain (5 preset buttons, chat input, messages with markdown, citation badges under each answer). Tab 2 Live Knowledge Mutator (form: supersedes id default `ADR-051`, new decision title, channel, system, rationale; button "Inject Decision into FalkorDB"; show returned latency and Cypher; hint to re-run Preset #2). Tab 3 Tenant Memory (private turns vs shared playbooks for the current persona).
  - **Right:** force graph on top, trace drawer below (every `agent_trace` step: agent, tool, Cypher in a monospace block, latency in ms).

### Behavior
- **Per-persona chat history.** Switching persona swaps the history, the `tenant_graph` label and Tab 3 data. Never show one persona's messages under another.
- **Graph rules:** node color by `type` (distinct color for Person, Team, System, Ticket, PullRequest, SlackThread, Document, Decision). `active` Decision/Document = green with a thick ring, `superseded` = red, `outdated` = amber. `SUPERSEDES` edges highlighted with arrows and labels. Legend included. Cap at ~60 nodes: keep citation nodes plus 1-hop neighbours. Empty subgraph -> placeholder. Resize the canvas to its container.
- **Citation badges** come from `citations[]` only, never parsed from the answer text: `ADR-051 active` green, `ADR-019 superseded` red, `source_ref` as small text.
- **Cold start handling:** Render may still be waking. On first load call `/health`; if slow or failing, show "Waking up the API, this can take ~30s" and retry with backoff. Do not show a raw error.
- **After a successful mutate:** clear the cached subgraph, show a success toast, and mark that Preset #2 should be re-run.
- **Errors:** map the error envelope to a readable message. 409 and 503 get their own wording.
- **`api.ts` mock fallback:** only when `NEXT_PUBLIC_USE_MOCK=true`; it returns canned payloads and flips the visible MOCK badge. Default is off.
- **Env:** `NEXT_PUBLIC_API_URL` (required), `NEXT_PUBLIC_USE_MOCK` (optional).
- Dark, clean "command center" look is fine; readability over flash. Basic a11y (button labels, focus states).

### Acceptance checks (manual, mirror the demo script)
1. Preset #1: answer names Kavya (`person-19`), graph shows system and people, trace shows `find_shadow_expert` and its Cypher.
2. Preset #2: DOC-082 flagged obsolete, ADR-051 green, ADR-019 red, `INC-204` and `SLACK-088` cited.
3. Tab 2 inject, then Preset #2: new ADR green, ADR-051 red.
4. Preset #3: 4-hop chain on the canvas and the leads to page listed.
5. Meera -> Riya: Tab 3 differs, `playbook-003` appears for Riya, chats are separate.
6. Stop the API (or wrong URL): UI shows a clear banner and does not crash.
7. `npm run build` passes with no type errors.

---

## 5. Step order for the coding agent

1. Read the docs and `models.py`. List contract mismatches (section 2) in `HANDOFF_TO_DEV_A.md`.
2. Backend: `schemas.py`, `backend.py` Protocol, `mock_bridge.py`, `deps.py`, `server.py`. Run `tests/test_04_api.py` green in mock mode.
3. Frontend scaffold: `npx create-next-app@14` with TS + Tailwind in `frontend/`, add `lib/types.ts` and `lib/api.ts`.
4. Build in this order: Header, Tab 1 + ForceGraph + TraceDrawer + CitationBadge, then Tab 2, then Tab 3, then ApiStatusBanner.
5. Run the manual checks against the local mock backend (`NEXUS_MODE=mock`).
6. Wire `LiveBackend` once Dev A merges Phase 2/3; rerun tests and checks with `NEXUS_MODE=live` against FalkorDB Cloud.
7. Deploy (section 6). Re-run the checks on the live URLs.
8. Update `README.md`: live demo links, architecture, quickstart, and only measured benchmark numbers.

---

## 6. Deployment checklist

**Order matters** (the API needs the Vercel URL for CORS, the UI needs the Render URL):

1. **FalkorDB Cloud:** create the instance, note host, port, username, password, and whether TLS is on.
2. **Render:** New Web Service -> GitHub repo -> Runtime Docker -> Free. Env vars: the `FALKORDB_*` set, `GEMINI_API_KEY` (optional), `NEXUS_MODE=live`, `CORS_ORIGINS=http://localhost:3000`. Health check path: `/api/v1/health`. Confirm the Dockerfile CMD uses `$PORT`.
3. **Vercel:** Import repo, Root Directory `frontend`, env `NEXT_PUBLIC_API_URL=<render url>`. Deploy.
4. **Back to Render:** add the Vercel production URL to `CORS_ORIGINS`, redeploy.
5. **Keep-alive:** UptimeRobot (every 5 min) or cron-job.org (every 10 min) hitting `/api/v1/health`. Free Render spins down after ~15 min idle; the monitor prevents it. Note that free instances have limited monthly hours, which one always-on service stays under.
6. Smoke test on the live URLs with the 7 checks above. Record the demo video **from the live deployment in live mode**.

---

## 7. Submission risks

- **Benchmarks:** README "actual" latencies (3.8 ms, 12 ms) must come from real runs on FalkorDB Cloud. Network latency to Render will make end-to-end turn time higher than 12 ms, so label server-side query time and end-to-end time separately.
- **Cold start:** if the monitor fails, the first judge request may take ~30s; the waking banner covers that.
- **Shared state:** judges mutate the same graph. Keep `/reset` handy before recording and consider the optional admin token.
- **Secrets:** never commit `.env`; only `.env.example`.
- FalkorDB must be central to the product, and the best blog post is a separate prize: draft it after the video.
