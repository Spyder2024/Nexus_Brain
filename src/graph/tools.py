"""Deterministic Cypher Query Engine for NexusBrain.

Implements the 5 parameterized, deterministic Cypher tool methods specified in TRD.md Section 5:
1. find_shadow_expert(system_name)
2. trace_decision_lineage(topic_or_system)
3. calculate_blast_radius(system_name)
4. mutate_knowledge_state(event_payload)
5. sync_agent_memory(user_id, turn_data)

Every method returns structured data, exact executed Cypher string, execution latency in ms,
and a visualizable subgraph container {nodes: [...], edges: [...]}.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.config import (
    get_company_graph,
    get_falkordb_client,
    settings,
)

logger = logging.getLogger("nexus_brain.graph.tools")


class GraphTools:
    """Deterministic, parameterized Cypher tool suite for agent interactions."""

    def __init__(self, company_graph=None, client=None):
        self.client = client or get_falkordb_client()
        self.company_graph = company_graph or get_company_graph()

    # -------------------------------------------------------------------------
    # Helper: Node & Edge parsing for Subgraph Visualization
    # -------------------------------------------------------------------------
    @staticmethod
    def _extract_node_dict(node: Any, default_type: str = "Node") -> Dict[str, Any]:
        """Convert FalkorDB Node object to frontend subgraph node format."""
        props = getattr(node, "properties", {}) if hasattr(node, "properties") else {}
        labels = getattr(node, "labels", []) if hasattr(node, "labels") else []
        node_type = labels[0] if labels else default_type

        node_id = props.get("id") or str(getattr(node, "id", "unknown"))
        label = props.get("name") or props.get("title") or props.get("id") or node_id
        status = props.get("status") or props.get("tier")

        return {
            "id": str(node_id),
            "label": str(label),
            "type": str(node_type),
            "status": str(status) if status else None,
        }

    # -------------------------------------------------------------------------
    # Tool 1: find_shadow_expert
    # -------------------------------------------------------------------------
    def find_shadow_expert(self, system_name: str) -> Dict[str, Any]:
        """Identify official maintainers vs actual high-impact contributors."""
        t0 = time.perf_counter()

        cypher = """
        MATCH (sys:System)
        WHERE sys.id = $sys_id OR sys.name = $sys_id
        OPTIONAL MATCH (official:Person)-[:MAINTAINS]->(sys)
        OPTIONAL MATCH (team:Team)-[:OWNS]->(sys)
        WITH sys, official, team

        OPTIONAL MATCH (p:Person)-[:ASSIGNED_TO]-(t:Ticket)-[:AFFECTS]->(sys)
        WHERE t.status = 'resolved'
        WITH sys, official, team, p, count(t) AS resolved_count,
             sum(CASE WHEN t.severity = 'SEV-1' THEN 3 WHEN t.severity = 'SEV-2' THEN 2 ELSE 1 END) AS sev_weight

        OPTIONAL MATCH (p)-[:AUTHORED]->(pr:PullRequest)-[:MODIFIES]->(sys)
        WITH sys, official, team, p, resolved_count, sev_weight, count(pr) AS pr_count
        WHERE p IS NOT NULL

        WITH sys, official, team, p, resolved_count, pr_count, (sev_weight + pr_count * 2) AS score
        ORDER BY score DESC
        RETURN sys, official, team, collect({person: p, resolved_tickets: resolved_count, prs: pr_count, score: score}) AS contributors
        """

        res = self.company_graph.query(cypher, {"sys_id": system_name})
        latency = (time.perf_counter() - t0) * 1000.0

        subgraph_nodes: Dict[str, Dict[str, Any]] = {}
        subgraph_edges: List[Dict[str, str]] = []

        official_info = {}
        top_contributors = []
        shadow_expert = None

        if res.result_set:
            row = res.result_set[0]
            sys_node = row[0]
            official_node = row[1]
            team_node = row[2]
            contributors_raw = row[3]

            if sys_node:
                s_dict = self._extract_node_dict(sys_node, "System")
                subgraph_nodes[s_dict["id"]] = s_dict

            if official_node:
                o_dict = self._extract_node_dict(official_node, "Person")
                subgraph_nodes[o_dict["id"]] = o_dict
                official_info = {
                    "id": o_dict["id"],
                    "name": official_node.properties.get("name"),
                    "role": official_node.properties.get("role"),
                    "team_id": official_node.properties.get("team_id"),
                }
                subgraph_edges.append({
                    "source": o_dict["id"],
                    "target": sys_node.properties.get("id"),
                    "relationship": "MAINTAINS",
                })

            if team_node:
                t_dict = self._extract_node_dict(team_node, "Team")
                subgraph_nodes[t_dict["id"]] = t_dict
                subgraph_edges.append({
                    "source": t_dict["id"],
                    "target": sys_node.properties.get("id"),
                    "relationship": "OWNS",
                })

            for item in contributors_raw:
                p_node = item.get("person")
                if not p_node:
                    continue
                p_dict = self._extract_node_dict(p_node, "Person")
                subgraph_nodes[p_dict["id"]] = p_dict
                contrib_entry = {
                    "person_id": p_dict["id"],
                    "name": p_node.properties.get("name"),
                    "role": p_node.properties.get("role"),
                    "team_id": p_node.properties.get("team_id"),
                    "resolved_tickets": item.get("resolved_tickets", 0),
                    "prs_authored": item.get("prs", 0),
                    "activity_score": item.get("score", 0),
                }
                top_contributors.append(contrib_entry)

                # Visual link
                subgraph_edges.append({
                    "source": p_dict["id"],
                    "target": sys_node.properties.get("id"),
                    "relationship": "ACTUAL_CONTRIBUTOR",
                })

            if top_contributors:
                # Top actual contributor
                shadow_expert = top_contributors[0]

        return {
            "system_name": system_name,
            "official_owner": official_info,
            "shadow_expert": shadow_expert,
            "top_contributors": top_contributors[:5],
            "cypher_executed": cypher.strip(),
            "latency_ms": round(latency, 2),
            "subgraph": {
                "nodes": list(subgraph_nodes.values()),
                "edges": subgraph_edges,
            },
        }

    # -------------------------------------------------------------------------
    # Tool 2: trace_decision_lineage
    # -------------------------------------------------------------------------
    def trace_decision_lineage(self, topic_or_system: str) -> Dict[str, Any]:
        """Trace active decision back through its superseding lineage, Slack debates, and tickets."""
        t0 = time.perf_counter()

        cypher = """
        OPTIONAL MATCH (d1:Decision)
        WHERE (d1.system_id = $val OR d1.topic = $val OR d1.id = $val) AND d1.status = 'active'
        OPTIONAL MATCH (target_doc:Document {id: $val})-[:CONTRADICTS]->(d2:Decision)
        WHERE d2.status = 'active'
        WITH coalesce(d1, d2) AS d
        WHERE d IS NOT NULL
        WITH d ORDER BY d.decided_at DESC LIMIT 1
        OPTIONAL MATCH path = (d)-[:SUPERSEDES*0..5]->(prev:Decision)
        OPTIONAL MATCH (d)<-[:TRIGGERED_DECISION]-(tk:Ticket)
        OPTIONAL MATCH (d)<-[:TRIGGERED_DECISION]-(st:SlackThread)
        OPTIONAL MATCH (doc:Document)-[:CONTRADICTS]->(d)
        RETURN d, collect(DISTINCT prev) AS lineage, collect(DISTINCT tk) AS tickets,
               collect(DISTINCT st) AS slack_threads, collect(DISTINCT doc) AS contradicting_docs
        """

        res = self.company_graph.query(cypher, {"val": topic_or_system})
        latency = (time.perf_counter() - t0) * 1000.0

        subgraph_nodes: Dict[str, Dict[str, Any]] = {}
        subgraph_edges: List[Dict[str, str]] = []

        active_decision = None
        superseded_chain = []
        linked_tickets = []
        linked_threads = []
        contradicting_docs = []

        if res.result_set:
            row = res.result_set[0]
            d_node = row[0]
            lineage_nodes = row[1]
            ticket_nodes = row[2]
            slack_nodes = row[3]
            doc_nodes = row[4]

            if d_node:
                active_dict = self._extract_node_dict(d_node, "Decision")
                subgraph_nodes[active_dict["id"]] = active_dict
                active_decision = {
                    "id": d_node.properties.get("id"),
                    "title": d_node.properties.get("title"),
                    "status": d_node.properties.get("status"),
                    "topic": d_node.properties.get("topic"),
                    "system_id": d_node.properties.get("system_id"),
                    "decided_at": d_node.properties.get("decided_at"),
                    "rationale": d_node.properties.get("rationale"),
                }

            # Superseded chain
            prev_id = active_dict["id"] if d_node else None
            for p_node in lineage_nodes:
                if not p_node or p_node.properties.get("id") == active_dict.get("id"):
                    continue
                p_dict = self._extract_node_dict(p_node, "Decision")
                subgraph_nodes[p_dict["id"]] = p_dict
                superseded_chain.append({
                    "id": p_node.properties.get("id"),
                    "title": p_node.properties.get("title"),
                    "status": p_node.properties.get("status"),
                    "decided_at": p_node.properties.get("decided_at"),
                    "invalidated_at": p_node.properties.get("invalidated_at"),
                    "rationale": p_node.properties.get("rationale"),
                })
                subgraph_edges.append({
                    "source": prev_id,
                    "target": p_dict["id"],
                    "relationship": "SUPERSEDES",
                })
                prev_id = p_dict["id"]

            for tk_node in ticket_nodes:
                if not tk_node:
                    continue
                tk_dict = self._extract_node_dict(tk_node, "Ticket")
                subgraph_nodes[tk_dict["id"]] = tk_dict
                linked_tickets.append({
                    "id": tk_node.properties.get("id"),
                    "title": tk_node.properties.get("title"),
                    "severity": tk_node.properties.get("severity"),
                })
                subgraph_edges.append({
                    "source": tk_dict["id"],
                    "target": active_dict["id"],
                    "relationship": "TRIGGERED_DECISION",
                })

            for st_node in slack_nodes:
                if not st_node:
                    continue
                st_dict = self._extract_node_dict(st_node, "SlackThread")
                subgraph_nodes[st_dict["id"]] = st_dict
                linked_threads.append({
                    "id": st_node.properties.get("id"),
                    "channel": st_node.properties.get("channel"),
                    "transcript": st_node.properties.get("transcript"),
                })
                subgraph_edges.append({
                    "source": st_dict["id"],
                    "target": active_dict["id"],
                    "relationship": "TRIGGERED_DECISION",
                })

            for doc_node in doc_nodes:
                if not doc_node:
                    continue
                doc_dict = self._extract_node_dict(doc_node, "Document")
                subgraph_nodes[doc_dict["id"]] = doc_dict
                contradicting_docs.append({
                    "id": doc_node.properties.get("id"),
                    "title": doc_node.properties.get("title"),
                    "status": doc_node.properties.get("status"),
                })
                subgraph_edges.append({
                    "source": doc_dict["id"],
                    "target": active_dict["id"],
                    "relationship": "CONTRADICTS",
                })

        return {
            "query": topic_or_system,
            "active_decision": active_decision,
            "superseded_chain": superseded_chain,
            "linked_tickets": linked_tickets,
            "linked_threads": linked_threads,
            "contradicting_documents": contradicting_docs,
            "cypher_executed": cypher.strip(),
            "latency_ms": round(latency, 2),
            "subgraph": {
                "nodes": list(subgraph_nodes.values()),
                "edges": subgraph_edges,
            },
        }

    # -------------------------------------------------------------------------
    # Tool 3: calculate_blast_radius
    # -------------------------------------------------------------------------
    def calculate_blast_radius(self, system_name: str) -> Dict[str, Any]:
        """Compute cascading downstream failure dependencies and impacted teams."""
        t0 = time.perf_counter()

        cypher = """
        MATCH (root:System)
        WHERE root.id = $sys_id OR root.name = $sys_id
        OPTIONAL MATCH (downstream:System)-[:DEPENDS_ON*1..4]->(root)
        OPTIONAL MATCH (t:Team)-[:OWNS]->(downstream)
        RETURN root, collect(DISTINCT downstream) AS downstream_systems, collect(DISTINCT t) AS affected_teams
        """

        res = self.company_graph.query(cypher, {"sys_id": system_name})
        latency = (time.perf_counter() - t0) * 1000.0

        subgraph_nodes: Dict[str, Dict[str, Any]] = {}
        subgraph_edges: List[Dict[str, str]] = []

        root_info = {}
        downstream_list = []
        teams_list = []

        if res.result_set:
            row = res.result_set[0]
            root_node = row[0]
            downstream_nodes = row[1]
            team_nodes = row[2]

            if root_node:
                r_dict = self._extract_node_dict(root_node, "System")
                subgraph_nodes[r_dict["id"]] = r_dict
                root_info = {
                    "id": root_node.properties.get("id"),
                    "name": root_node.properties.get("name"),
                    "tier": root_node.properties.get("tier"),
                }

            # Fetch exact dependency paths for edge rendering
            path_query = """
            MATCH path = (downstream:System)-[:DEPENDS_ON*1..4]->(root:System)
            WHERE root.id = $sys_id OR root.name = $sys_id
            RETURN relationships(path) AS rels, nodes(path) AS path_nodes
            """
            p_res = self.company_graph.query(path_query, {"sys_id": system_name})
            for p_row in p_res.result_set:
                p_nodes = p_row[1]
                for i in range(len(p_nodes) - 1):
                    src_n = p_nodes[i]
                    tgt_n = p_nodes[i + 1]
                    s_id = src_n.properties.get("id")
                    t_id = tgt_n.properties.get("id")
                    subgraph_nodes[s_id] = self._extract_node_dict(src_n, "System")
                    subgraph_nodes[t_id] = self._extract_node_dict(tgt_n, "System")
                    edge_tuple = {"source": s_id, "target": t_id, "relationship": "DEPENDS_ON"}
                    if edge_tuple not in subgraph_edges:
                        subgraph_edges.append(edge_tuple)

            for d_node in downstream_nodes:
                if not d_node:
                    continue
                d_dict = self._extract_node_dict(d_node, "System")
                subgraph_nodes[d_dict["id"]] = d_dict
                downstream_list.append({
                    "id": d_node.properties.get("id"),
                    "name": d_node.properties.get("name"),
                    "tier": d_node.properties.get("tier"),
                    "owner_team": d_node.properties.get("owner_team_id"),
                })

            for t_node in team_nodes:
                if not t_node:
                    continue
                t_dict = self._extract_node_dict(t_node, "Team")
                subgraph_nodes[t_dict["id"]] = t_dict
                teams_list.append({
                    "id": t_node.properties.get("id"),
                    "name": t_node.properties.get("name"),
                    "lead_id": t_node.properties.get("lead_id"),
                    "slack_channel": t_node.properties.get("slack_channel"),
                })

        return {
            "root_system": root_info,
            "blast_radius_depth": 4,
            "downstream_systems_count": len(downstream_list),
            "downstream_systems": downstream_list,
            "affected_teams": teams_list,
            "cypher_executed": cypher.strip(),
            "latency_ms": round(latency, 2),
            "subgraph": {
                "nodes": list(subgraph_nodes.values()),
                "edges": subgraph_edges,
            },
        }

    # -------------------------------------------------------------------------
    # Tool 4: mutate_knowledge_state (Temporal Scribe)
    # -------------------------------------------------------------------------
    def mutate_knowledge_state(self, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Temporal Scribe tool: supercedes old decision and creates new active ADR node."""
        t0 = time.perf_counter()
        now_iso = datetime.now(timezone.utc).isoformat()

        supersedes_id = event_payload.get("supersedes_id") or event_payload.get("supersedes_decision_id")
        target_system = event_payload.get("system_id") or "auth-service"

        # If supersedes_id not specified, find currently active decision for target system
        if not supersedes_id:
            find_active = self.company_graph.query(
                "MATCH (d:Decision {system_id: $sys, status: 'active'}) RETURN d.id LIMIT 1",
                {"sys": target_system},
            )
            if find_active.result_set:
                supersedes_id = find_active.result_set[0][0]
            else:
                supersedes_id = "ADR-051"

        new_id = (
            event_payload.get("decision_id")
            or event_payload.get("new_decision_id")
            or f"ADR-{int(time.time()) % 10000:04d}"
        )
        title = event_payload.get("title") or event_payload.get("new_decision_title") or "New Architecture Evolution Decision"
        rationale = event_payload.get("rationale") or "Superseding previous architecture standard via live agent mutation."
        author_id = event_payload.get("author_id") or "person-19"

        cypher = """
        MATCH (old:Decision {id: $supersedes_id})
        SET old.status = 'superseded', old.invalidated_at = $now_iso
        WITH old
        CREATE (new:Decision {
            id: $new_id,
            title: $title,
            topic: old.topic,
            status: 'active',
            decided_at: $now_iso,
            author_id: $author_id,
            system_id: old.system_id,
            rationale: $rationale,
            supersedes_decision_id: old.id
        })
        CREATE (new)-[:SUPERSEDES {transition_date: $now_iso, reason: $rationale}]->(old)
        WITH old, new
        MATCH (s:System {id: old.system_id})
        MERGE (new)-[:AFFECTS {status: 'active'}]->(s)
        RETURN old, new, s
        """

        params = {
            "supersedes_id": supersedes_id,
            "new_id": new_id,
            "title": title,
            "rationale": rationale,
            "author_id": author_id,
            "now_iso": now_iso,
        }

        res = self.company_graph.query(cypher, params)
        latency = (time.perf_counter() - t0) * 1000.0

        subgraph_nodes = []
        subgraph_edges = []

        if res.result_set:
            old_node, new_node, sys_node = res.result_set[0]
            old_dict = self._extract_node_dict(old_node, "Decision")
            new_dict = self._extract_node_dict(new_node, "Decision")
            sys_dict = self._extract_node_dict(sys_node, "System")

            subgraph_nodes = [new_dict, old_dict, sys_dict]
            subgraph_edges = [
                {"source": new_dict["id"], "target": old_dict["id"], "relationship": "SUPERSEDES"},
                {"source": new_dict["id"], "target": sys_dict["id"], "relationship": "AFFECTS"},
            ]

        return {
            "status": "success",
            "success": True,
            "new_decision_id": new_id,
            "superseded_decision_id": supersedes_id,
            "mutated_at": now_iso,
            "cypher_executed": cypher.strip(),
            "latency_ms": round(latency, 2),
            "subgraph": {
                "nodes": subgraph_nodes,
                "edges": subgraph_edges,
            },
        }

    # -------------------------------------------------------------------------
    # Tool 5: sync_agent_memory (Tenant Isolation)
    # -------------------------------------------------------------------------
    def sync_agent_memory(self, user_id: str, turn_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Read and write episodic turns and procedural playbooks in isolated tenant multigraph."""
        t0 = time.perf_counter()
        tenant_graph_name = f"{settings.TENANT_GRAPH_PREFIX}{user_id}"
        tenant_graph = self.client.select_graph(tenant_graph_name)

        now_iso = datetime.now(timezone.utc).isoformat()
        executed_cyphers: List[str] = []

        # If turn_data provided, write episodic turn
        if turn_data:
            session_id = turn_data.get("session_id") or f"session-{user_id}"
            turn_id = turn_data.get("turn_id") or f"turn-{int(time.time() * 1000)}"
            role = turn_data.get("role") or "user"
            content = turn_data.get("content") or ""
            ref_ids = turn_data.get("referenced_node_ids") or []

            write_cypher = """
            MERGE (s:Session {id: $session_id, user_id: $user_id})
            ON CREATE SET s.started_at = $now_iso
            CREATE (t:Turn {
                id: $turn_id,
                session_id: $session_id,
                role: $role,
                content: $content,
                timestamp: $now_iso,
                referenced_node_ids: $ref_ids
            })
            CREATE (s)-[:HAS_TURN]->(t)
            RETURN s, t
            """
            tenant_graph.query(
                write_cypher,
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "turn_id": turn_id,
                    "role": role,
                    "content": content,
                    "now_iso": now_iso,
                    "ref_ids": ref_ids,
                },
            )
            executed_cyphers.append(write_cypher.strip())

            # Optional: store procedural playbook if provided
            if "playbook" in turn_data:
                pb = turn_data["playbook"]
                pb_id = pb.get("id") or f"playbook-{int(time.time())}"
                pb_cypher = """
                MERGE (p:Playbook {id: $pb_id})
                SET p.trigger_signature = $trigger,
                    p.resolution_steps = $steps,
                    p.verified_by_ticket_id = $ticket_id,
                    p.success_count = coalesce(p.success_count, 0) + 1
                RETURN p
                """
                tenant_graph.query(
                    pb_cypher,
                    {
                        "pb_id": pb_id,
                        "trigger": pb.get("trigger_signature", ""),
                        "steps": pb.get("resolution_steps", []),
                        "ticket_id": pb.get("verified_by_ticket_id", ""),
                    },
                )
                executed_cyphers.append(pb_cypher.strip())

        # Read episodic history & playbooks
        read_cypher = """
        OPTIONAL MATCH (s:Session)-[:HAS_TURN]->(t:Turn)
        OPTIONAL MATCH (p:Playbook)
        RETURN collect(DISTINCT t) AS turns, collect(DISTINCT p) AS playbooks
        """
        read_res = tenant_graph.query(read_cypher)
        executed_cyphers.append(read_cypher.strip())

        turns_list = []
        playbooks_list = []
        subgraph_nodes = []
        subgraph_edges = []

        if read_res.result_set:
            turns_nodes, pb_nodes = read_res.result_set[0]
            for t_node in turns_nodes:
                if not t_node:
                    continue
                t_dict = self._extract_node_dict(t_node, "Turn")
                subgraph_nodes.append(t_dict)
                turns_list.append({
                    "id": t_node.properties.get("id"),
                    "role": t_node.properties.get("role"),
                    "content": t_node.properties.get("content"),
                    "timestamp": t_node.properties.get("timestamp"),
                })
            for p_node in pb_nodes:
                if not p_node:
                    continue
                p_dict = self._extract_node_dict(p_node, "Playbook")
                subgraph_nodes.append(p_dict)
                playbooks_list.append({
                    "id": p_node.properties.get("id"),
                    "trigger_signature": p_node.properties.get("trigger_signature"),
                    "resolution_steps": p_node.properties.get("resolution_steps"),
                    "success_count": p_node.properties.get("success_count"),
                })

        latency = (time.perf_counter() - t0) * 1000.0

        return {
            "tenant_graph": tenant_graph_name,
            "user_id": user_id,
            "turns_count": len(turns_list),
            "recent_turns": turns_list[-10:],
            "playbooks": playbooks_list,
            "cypher_executed": "\n---\n".join(executed_cyphers),
            "latency_ms": round(latency, 2),
            "subgraph": {
                "nodes": subgraph_nodes,
                "edges": subgraph_edges,
            },
        }
