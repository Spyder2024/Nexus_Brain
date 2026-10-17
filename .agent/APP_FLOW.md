# Application Flow (APP_FLOW.md): NexusBrain

## 1. Core Screen Layout (Split-Pane Command Center)
The UI operates as a single-page unified workspace divided into 3 zones:
- **Top Header Bar:**
  - **Tenant / Persona Switcher Dropdown:** Switch between `User 1: Kabir (ML Lead)`, `User 2: Meera (SRE On-Call)`, and `User 3: Riya (New Grad Hire)`. Changing this switches the active FalkorDB multigraph (`memory_tenant_{user_id}`).
  - **FalkorDB Connection Badge:** Shows live node count, edge count, and query latency in ms.
- **Left Pane (45% width): Interactive Agent Console & Live Mutator**
  - **Tab 1: Ask the Company Brain:** Chat interface + 5 One-Click "Golden Scenario" Preset Buttons + Citation Cards below each response.
  - **Tab 2: Live Knowledge Mutator (Real-Time Ingestion):** Form to inject a live Slack message, Incident Ticket, or PR to demonstrate real-time temporal graph updates.
  - **Tab 3: Agent Memory & Handoff Inspector:** Shows Episodic turns and Procedural Playbooks stored in the current user's isolated tenant graph.
- **Right Pane (55% width): Live FalkorDB Trace Visualizer**
  - **Top Canvas (70% height):** Interactive force-directed subgraph showing exact nodes and directed edges traversed for the current answer. Active decisions glow solid green; superseded/outdated nodes render with dashed amber/red borders.
  - **Bottom Drawer (30% height):** Multi-Agent Handoff Log & exact executed Cypher queries with execution time (`ms`).

---

## 2. Primary User Flows (The 4 Demo Acts)

### Flow A: Multi-Hop Provenance & Shadow Expert Discovery
1. User clicks Preset #1: *"Who actually knows the most about `auth-service` outages, and what breaks if it goes down?"*
2. `RouterAgent` dispatches `find_shadow_expert("auth-service")` and `calculate_blast_radius("auth-service")` to `GraphNavigator`.
3. `GraphNavigator` executes multi-hop Cypher queries on `company_brain`.
4. **UI Update:**
   - Left pane explains that while `Person_04` is the official lead, `Person_19` resolved 18 critical `SEV-1` tickets and 25 PRs, and lists the 3 downstream systems (`checkout-orchestrator`, etc.) at risk.
   - Right pane renders the exact dependency and contribution subgraph.

### Flow B: Temporal Decision Lineage (Detecting Outdated Docs)
1. User clicks Preset #2: *"Can I use Kafka for synchronous RPC as written in Onboarding Doc DOC-004?"*
2. `GraphNavigator` runs `trace_decision_lineage` and detects that `DOC-004` references `ADR-019` (`status: superseded`), which was replaced by `ADR-051` after deadlock incident `INC-204` and Slack thread `SLACK-088`.
3. **UI Update:**
   - Agent warns the user NOT to follow `DOC-004`, cites `ADR-051` and `SLACK-088`, and highlights the `[:SUPERSEDES]` chain on the graph canvas.

### Flow C: Live Knowledge Mutation (Real-Time Graph Update)
1. User switches to **Tab 2 (Live Knowledge Mutator)**.
2. User clicks **"Simulate Breaking Slack Decision"** (or pastes a Slack snippet): *"In #arch-sync: Due to Envoy proxy bug INC-299, we are superseding ADR-051 and moving auth-service RPC to HTTP/3."*
3. `MemoryScribe` extracts entities, creates `ADR-061 (status: active)`, flips `ADR-051` to `status: superseded`, and links `(ADR-061)-[:SUPERSEDES]->(ADR-051)`.
4. User returns to **Tab 1** and re-asks the exact same question from Flow B.
5. **UI Update:** The agent immediately returns the new HTTP/3 decision (`ADR-061`) and visually shows `ADR-051` marked as superseded.

### Flow D: Cross-Session Multi-Tenant Memory & Agent Handoff
1. User selects `Meera (SRE On-Call)` in the Top Header and resolves an incident on `ml-inference-worker`.
2. `MemoryScribe` saves the episodic turn in `memory_tenant_meera` AND promotes the fix to a shared `(:Playbook)` node.
3. User switches persona to `Riya (New Hire)` -> `memory_tenant_riya` has a clean episodic chat history, but Riya's agent automatically inherits the verified `(:Playbook)` created during Meera's session.