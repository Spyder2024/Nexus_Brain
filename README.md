# ⚡ NexusBrain: Enterprise Knowledge Graph & Multi-Agent Cognitive Engine

> **FalkorDB Graph Hacks Hackathon Entry**
> * **Track 03:** Company Brain (Cross-silo Enterprise Graph Intelligence)
> * **Track 02:** Agent Memory & Multi-Agent Coordination

---

## 📌 Overview
**NexusBrain** breaks down enterprise knowledge silos (Jira, GitHub, Slack, Documentation, Architecture Decisions) and turns them into an interconnected, queryable **Graph-Native Company Brain** powered by **FalkorDB**.

Instead of isolated tools where context is lost, NexusBrain models organizational relationships as a high-fidelity directed graph—enabling multi-agent systems to perform deep causal tracing, blast-radius analysis, and semantic incident memory retrieval.

```
       ┌────────────────────────────────────────────────────────┐
       │             NexusBrain Multi-Agent Engine              │
       │   RouterAgent  ───►  GraphNavigator  ───►  MemoryScribe│
       └──────────────┬─────────────────────────────┬───────────┘
                      │                             │
                      ▼                             ▼
       ┌──────────────────────────────┐ ┌────────────────────────┐
       │  company_brain (FalkorDB)    │ │ memory_tenant_{user_id}│
       │  - 1,077 Org & Code Nodes    │ │ - Episodic Turn History│
       │  - 4,103 Multi-Hop Edges     │ │ - Reusable Playbooks   │
       │  - Bi-Temporal ADR Chains    │ │ - Multi-Tenant Private │
       └──────────────────────────────┘ └────────────────────────┘
```

---

## 🏗️ Architecture & Schema
NexusBrain models **"7bit Cloud Technologies"**, a realistic AI/Cloud SaaS enterprise:

### Node Types (1,077 Nodes):
* **`Team` (8):** Core Platform, Auth & Identity, Payment & Billing, ML Inference, Data Pipeline, SRE & Infra, Frontend Experience, Security & Compliance.
* **`Person` (65):** Staff engineers, architects, managers with skills, seniority, and tenure.
* **`System` (24):** Tier-0 to Tier-3 microservices, data stores, caches, and gateways.
* **`Ticket` (250):** SEV-1 to SEV-4 Jira/Linear incidents, bugs, features, and tech debt.
* **`PullRequest` (400):** GitHub PRs linked to tickets, files changed, and code reviewers.
* **`SlackThread` (180):** Multi-turn incident war-rooms, architecture debates, and sign-offs.
* **`Document` (90):** Runbooks, RFCs, postmortems, and onboarding guides (active vs. outdated).
* **`Decision` (60):** Architecture Decision Records (ADRs) organized into **20 Temporal Evolution Chains**.

### Edge Topology (4,103 Directed Edges):
* **Organization:** `MEMBER_OF`, `LEADS`, `OWNS`, `MAINTAINS`, `DEPENDS_ON`
* **Incidents & Issues:** `REPORTED`, `ASSIGNED_TO`, `AFFECTS`, `CAUSED_BY`
* **Engineering & Code:** `AUTHORED`, `REVIEWED`, `IMPLEMENTS`, `RESOLVES`, `MODIFIES`
* **Conversations & Decisions:** `PARTICIPATED_IN`, `DISCUSSES`, `TRIGGERED_DECISION`
* **Temporal Dynamics:** `SUPERSEDES`, `CONTRADICTS`, `GUIDES_RESOLUTION_OF`

---

## 🏆 5 Planted "Golden Demo Scenarios"
Hardcoded into the simulation engine to showcase multi-hop graph reasoning:

1. **The Hidden Subject-Matter Expert (Shadow Ownership):**
   * Officially, `person-04` leads `auth-service`, but `person-19` (an SRE) resolved 18 critical SEV-1 tickets and authored 26 PRs on `auth-service` over the last 60 days.
2. **The Temporal Decision Flip (Knowledge Evolution):**
   * An onboarding doc (`DOC-082`) still says "Use Kafka for synchronous RPC," which was superseded by `ADR-051` in Slack `#arch-sync` (`SLACK-088`) after incident `INC-204` caused a deadlock.
3. **The 4-Hop Cascading Blast Radius:**
   * `redis-session-store` OOM evictions cascade to `auth-token-validator` $\rightarrow$ `checkout-orchestrator` $\rightarrow$ `stripe-webhook-worker`, impacting 3 separate teams (captured in `INC-119`).
4. **Cross-Agent Incident Memory:**
   * A recurring CUDA memory leak in `ml-inference-worker` happened 4 months ago (`INC-045`), was mitigated via runbook `DOC-012`, and resurfaced in `INC-249`.
5. **The Undocumented API Breaking Change:**
   * `PR-398` modified `user-profile-service` schemas without updating downstream consumer `recommendation-service`, triggering deserialization panic `INC-250`.

---

## 🚀 Quickstart

### 1. Prerequisites
* Python 3.12+
* Docker & Docker Compose (optional for in-memory fallback, recommended for live FalkorDB)

### 2. Setup Environment
```bash
# Clone repository
git clone https://github.com/Spyder2024/Nexus_Brain.git
cd Nexus_Brain

# Install dependencies
pip install -r requirements.txt
```

### 3. Start FalkorDB (Optional for live graph protocol)
```bash
docker compose up -d
```
* **FalkorDB Cypher Protocol:** `localhost:6379`
* **FalkorDB Web Browser:** `http://localhost:3000`

### 4. Start the FastAPI Backend
```bash
python -m src.api.server
```
API Documentation will be live at `http://localhost:8000/docs`.

### 5. Launch the Command Center UI
In a separate terminal:
```bash
streamlit run src/ui/app.py
```
Open your browser at `http://localhost:8501`.

---

## 🎮 The 4 Demo Acts (Judge Walkthrough)

1. **Act A: Shadow Ownership Discovery**
   - Click Preset Button 1: *"Who actually knows the most about auth-service outages?"*
   - See how the graph identifies `person-19` over the official lead and lists downstream blast radius.
2. **Act B: Stale Documentation Catch**
   - Click Preset Button 2: *"Can I use Kafka for synchronous RPC as written in DOC-082?"*
   - Watch the agent warn against the outdated doc, citing `ADR-051` and war-room `SLACK-088`.
3. **Act C: Live Real-Time Knowledge Mutation**
   - Switch to **Tab 2 (Live Knowledge Mutator)**.
   - Inject the breaking Slack decision moving RPC to HTTP/3 QUIC (`ADR-061`).
   - Switch back to **Tab 1** and re-run Preset 2 — the agent immediately adapts, showing `ADR-051` as superseded and `ADR-061` glowing active green on the graph canvas!
4. **Act D: Cross-Session Tenant Memory Handoff**
   - Switch top persona between **Meera (SRE)** and **Riya (New Hire)**.
   - Inspect **Tab 3** to see how verified procedural playbooks (`playbook-003`) survive across tenants while preserving private episodic chat turns.

---

## 📂 Project Structure
```text
nexus_brain/
├── data/
│   ├── raw/                  # JSON silos & unified graph bundle
│   └── processed/            # Tabular node/edge inspection CSVs
├── src/
│   ├── config.py             # OS-agnostic configuration & settings
│   ├── schema/               # Pydantic v2 graph schemas & API contracts
│   ├── data_gen/             # Deterministic enterprise dataset generator
│   ├── graph/                # FalkorDB loader & Cypher query engine
│   ├── agents/               # Multi-agent coordination engine
│   ├── api/                  # FastAPI REST endpoints & mock bridge
│   │   ├── server.py
│   │   └── mock_bridge.py
│   └── ui/                   # Streamlit visual command center
│       ├── app.py
│       └── graph_viz.py
├── docker-compose.yml        # FalkorDB local deployment
├── requirements.txt
└── README.md
```
