"""Specialized Multi-Agent Specialists for NexusBrain.

Implements the three core cooperating agents specified in TRD.md Section 5:
1. RouterAgent:
   - Intent classification & entity extraction.
   - Dual-mode execution (Optional LLM tool-calling with deterministic fast fallback).
   - Anaphora / pronoun resolution using episodic session memory.
2. GraphNavigator:
   - Executes deterministic parameterized Cypher tools via GraphTools.
   - Merges & deduplicates subgraphs across multi-tool invocations.
   - Extracts structured CitationItem references (active vs superseded).
3. MemoryScribe:
   - Manages episodic conversation history in isolated multigraph memory_tenant_{user_id}.
   - Procedural memory promotion: turns runbooks and verified incident resolutions into reusable Playbook nodes.
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from src.agents.models import (
    AgentTraceStep,
    CitationItem,
    SubgraphEdge,
    SubgraphNode,
    SubgraphPayload,
)
from src.config import settings
from src.graph.tools import GraphTools

logger = logging.getLogger("nexus_brain.agents.specialists")


# -----------------------------------------------------------------------------
# 1. RouterAgent
# -----------------------------------------------------------------------------
class RouterAgent:
    """Intelligent router that determines tools and entity targets from query + session memory."""

    KNOWN_SYSTEMS = [
        "auth-service", "redis-session-store", "auth-token-validator", "kafka-event-bus",
        "redis-state-cluster", "vector-gateway", "billing-ledger", "checkout-orchestrator",
        "stripe-webhook-worker", "user-profile-service", "recommendation-service",
        "ml-inference-worker", "model-registry-service", "feature-store-api",
        "data-lakehouse-ingest", "event-stream-enricher", "metrics-aggregation-pipeline",
        "frontend-bff-gateway", "web-client-spa", "admin-console-service", "audit-log-vault",
        "secrets-kms-proxy", "network-mesh-ingress", "cloud-cost-optimizer",
    ]

    TOPIC_KEYWORDS = {
        "kafka": ("Inter-Service RPC Protocol", "auth-service"),
        "rpc": ("Inter-Service RPC Protocol", "auth-service"),
        "grpc": ("Inter-Service RPC Protocol", "auth-service"),
        "cuda": ("ml-inference-worker", "ml-inference-worker"),
        "oom": ("ml-inference-worker", "ml-inference-worker"),
        "memory leak": ("ml-inference-worker", "ml-inference-worker"),
        "breaking change": ("user-profile-service", "user-profile-service"),
        "deserialization": ("recommendation-service", "recommendation-service"),
        "checkout": ("checkout-orchestrator", "checkout-orchestrator"),
        "session": ("redis-session-store", "redis-session-store"),
        "token": ("auth-token-validator", "auth-token-validator"),
    }

    def __init__(self):
        pass

    def route(self, query: str, recent_entities: Optional[List[str]] = None) -> Dict[str, Any]:
        """Determine tool execution plan using deterministic entity + intent extraction."""
        t0 = time.perf_counter()
        query_lower = query.lower()
        recent_entities = recent_entities or []

        # 1. Extract Target System or Entity
        target_system: Optional[str] = None
        for s in self.KNOWN_SYSTEMS:
            if s.lower() in query_lower or s.replace("-", " ") in query_lower:
                target_system = s
                break

        # Check explicit ID patterns (e.g. DOC-082, ADR-051, INC-204, PR-398)
        id_match = re.search(r"\b(ADR-\d+|DOC-\d+|INC-\d+|PR-\d+|SLACK-\d+)\b", query, re.IGNORECASE)
        explicit_id = id_match.group(1).upper() if id_match else None

        # Resolve pronouns / follow-up context if target_system not found
        if not target_system and any(p in query_lower for p in [" it ", " its ", " that ", " this ", "the service"]):
            for prev_ent in recent_entities:
                if prev_ent in self.KNOWN_SYSTEMS:
                    target_system = prev_ent
                    break

        # Check topic keywords
        detected_topic = None
        for kw, (topic_name, default_sys) in self.TOPIC_KEYWORDS.items():
            if kw in query_lower:
                detected_topic = topic_name
                if not target_system:
                    target_system = default_sys
                break

        # Fallback default if still None
        if not target_system and not explicit_id and not detected_topic:
            target_system = recent_entities[0] if recent_entities else "auth-service"

        # 2. Determine Required Tools
        tools_to_run: List[Dict[str, Any]] = []

        is_shadow_query = any(w in query_lower for w in [
            "who knows", "who actually", "expert", "maintain", "owner", "shadow", "who worked", "who fixed"
        ])
        is_blast_query = any(w in query_lower for w in [
            "blast radius", "what breaks", "downstream", "cascading", "impact", "fail", "goes down"
        ])
        is_decision_query = any(w in query_lower for w in [
            "can i use", "decision", "adr", "lineage", "doc-", "outdated", "supersede", "why did we change", "protocol", "rpc", "standard"
        ]) or (explicit_id and ("ADR" in explicit_id or "DOC" in explicit_id))

        if is_shadow_query and is_blast_query:
            tools_to_run.append({"tool": "find_shadow_expert", "arg": target_system})
            tools_to_run.append({"tool": "calculate_blast_radius", "arg": target_system})
        elif is_shadow_query:
            tools_to_run.append({"tool": "find_shadow_expert", "arg": target_system})
        elif is_blast_query:
            tools_to_run.append({"tool": "calculate_blast_radius", "arg": target_system})
        elif is_decision_query:
            decision_arg = explicit_id or detected_topic or target_system
            tools_to_run.append({"tool": "trace_decision_lineage", "arg": decision_arg})
        else:
            # Default to decision lineage or shadow expert based on content
            if "who" in query_lower:
                tools_to_run.append({"tool": "find_shadow_expert", "arg": target_system})
            else:
                tools_to_run.append({"tool": "trace_decision_lineage", "arg": detected_topic or target_system})

        latency = (time.perf_counter() - t0) * 1000.0

        return {
            "target_system": target_system,
            "explicit_id": explicit_id,
            "detected_topic": detected_topic,
            "tools_to_run": tools_to_run,
            "latency_ms": round(latency, 2),
        }


# -----------------------------------------------------------------------------
# 2. GraphNavigator
# -----------------------------------------------------------------------------
class GraphNavigator:
    """Executes deterministic Cypher queries on FalkorDB and collects unified graph traces."""

    def __init__(self, tools: Optional[GraphTools] = None):
        self.tools = tools or GraphTools()

    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all planned tool calls, collecting results, traces, citations, and merged subgraphs."""
        traces: List[AgentTraceStep] = []
        citations: List[CitationItem] = []
        nodes_map: Dict[str, SubgraphNode] = {}
        edges_set: Set[Tuple[str, str, str]] = set()

        raw_results: Dict[str, Any] = {}

        for step in plan.get("tools_to_run", []):
            tool_name = step["tool"]
            arg = step["arg"]

            if tool_name == "find_shadow_expert":
                res = self.tools.find_shadow_expert(arg)
                raw_results["shadow_expert_result"] = res
                traces.append(AgentTraceStep(
                    agent="GraphNavigator",
                    tool="find_shadow_expert",
                    cypher_executed=res["cypher_executed"],
                    latency_ms=res["latency_ms"],
                ))
                # Citations
                if res.get("official_owner"):
                    o = res["official_owner"]
                    citations.append(CitationItem(
                        id=o["id"],
                        label="Person",
                        title=f"{o['name']} ({o['role']})",
                        status="official_maintainer",
                        source_ref=arg,
                    ))
                if res.get("shadow_expert"):
                    s = res["shadow_expert"]
                    citations.append(CitationItem(
                        id=s["person_id"],
                        label="Person",
                        title=f"{s['name']} (SRE Actual Contributor)",
                        status="shadow_expert",
                        source_ref=f"{s['resolved_tickets']} SEV-1s, {s['prs_authored']} PRs",
                    ))
                self._merge_subgraph(res.get("subgraph", {}), nodes_map, edges_set)

            elif tool_name == "calculate_blast_radius":
                res = self.tools.calculate_blast_radius(arg)
                raw_results["blast_radius_result"] = res
                traces.append(AgentTraceStep(
                    agent="GraphNavigator",
                    tool="calculate_blast_radius",
                    cypher_executed=res["cypher_executed"],
                    latency_ms=res["latency_ms"],
                ))
                for sys in res.get("downstream_systems", []):
                    citations.append(CitationItem(
                        id=sys["id"],
                        label="System",
                        title=sys["name"],
                        status=sys["tier"],
                        source_ref=f"Owner: {sys['owner_team']}",
                    ))
                for t in res.get("affected_teams", []):
                    citations.append(CitationItem(
                        id=t["id"],
                        label="Team",
                        title=t["name"],
                        status="affected_team",
                        source_ref=t.get("slack_channel"),
                    ))
                self._merge_subgraph(res.get("subgraph", {}), nodes_map, edges_set)

            elif tool_name == "trace_decision_lineage":
                res = self.tools.trace_decision_lineage(arg)
                raw_results["decision_lineage_result"] = res
                traces.append(AgentTraceStep(
                    agent="GraphNavigator",
                    tool="trace_decision_lineage",
                    cypher_executed=res["cypher_executed"],
                    latency_ms=res["latency_ms"],
                ))
                if res.get("active_decision"):
                    ad = res["active_decision"]
                    citations.append(CitationItem(
                        id=ad["id"],
                        label="Decision",
                        title=ad["title"],
                        status="active",
                        source_ref=ad.get("system_id"),
                    ))
                for sd in res.get("superseded_chain", []):
                    citations.append(CitationItem(
                        id=sd["id"],
                        label="Decision",
                        title=sd["title"],
                        status="superseded",
                        source_ref=sd.get("invalidated_at"),
                    ))
                for doc in res.get("contradicting_documents", []):
                    citations.append(CitationItem(
                        id=doc["id"],
                        label="Document",
                        title=doc["title"],
                        status=doc["status"],
                        source_ref="CONTRADICTS active decision",
                    ))
                for tk in res.get("linked_tickets", []):
                    citations.append(CitationItem(
                        id=tk["id"],
                        label="Ticket",
                        title=tk["title"],
                        status=tk.get("severity", "incident"),
                        source_ref="TRIGGERED_DECISION",
                    ))
                for st in res.get("linked_threads", []):
                    citations.append(CitationItem(
                        id=st["id"],
                        label="SlackThread",
                        title=st["channel"],
                        status="discussion",
                        source_ref="Consensus thread",
                    ))
                self._merge_subgraph(res.get("subgraph", {}), nodes_map, edges_set)

        # Build merged SubgraphPayload
        merged_edges = [
            SubgraphEdge(source=s, target=t, relationship=r)
            for (s, t, r) in edges_set
        ]
        subgraph = SubgraphPayload(
            nodes=list(nodes_map.values()),
            edges=merged_edges,
        )

        return {
            "raw_results": raw_results,
            "traces": traces,
            "citations": citations,
            "subgraph": subgraph,
        }

    @staticmethod
    def _merge_subgraph(
        sg: Dict[str, Any],
        nodes_map: Dict[str, SubgraphNode],
        edges_set: Set[Tuple[str, str, str]],
    ):
        """Deduplicate nodes and edges into shared maps."""
        for n in sg.get("nodes", []):
            nid = n.get("id")
            if nid and nid not in nodes_map:
                nodes_map[nid] = SubgraphNode(
                    id=str(nid),
                    label=str(n.get("label", nid)),
                    type=str(n.get("type", "Node")),
                    status=n.get("status"),
                    properties=n.get("properties"),
                )
        for e in sg.get("edges", []):
            s = e.get("source")
            t = e.get("target")
            r = e.get("relationship", "RELATES_TO")
            if s and t:
                edges_set.add((str(s), str(t), str(r)))


# -----------------------------------------------------------------------------
# 3. MemoryScribe
# -----------------------------------------------------------------------------
class MemoryScribe:
    """Manages isolated tenant episodic history and procedural playbook evolution."""

    def __init__(self, tools: Optional[GraphTools] = None):
        self.tools = tools or GraphTools()

    def get_context(self, user_id: str) -> Dict[str, Any]:
        """Fetch recent turns and active playbooks from memory_tenant_{user_id}."""
        res = self.tools.sync_agent_memory(user_id=user_id, turn_data=None)

        recent_entities: List[str] = []
        for t in res.get("recent_turns", []):
            # Extract mentions of IDs in turn content
            words = t.get("content", "").split()
            for w in words:
                clean_w = w.strip("[](),.:'\"")
                if clean_w in RouterAgent.KNOWN_SYSTEMS or any(clean_w.startswith(p) for p in ["ADR-", "DOC-", "INC-", "PR-", "person-"]):
                    recent_entities.append(clean_w)

        return {
            "tenant_graph": res["tenant_graph"],
            "turns_count": res["turns_count"],
            "recent_turns": res.get("recent_turns", []),
            "playbooks": res.get("playbooks", []),
            "recent_entities": list(dict.fromkeys(recent_entities)),
        }

    def record_turn(
        self,
        user_id: str,
        query: str,
        answer: str,
        referenced_node_ids: List[str],
        session_id: Optional[str] = None,
        promoted_playbook: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record completed conversation turn in isolated tenant graph."""
        sess_id = session_id or f"session-{user_id}"

        turn_payload = {
            "session_id": sess_id,
            "turn_id": f"turn-{int(time.time() * 1000)}",
            "role": "assistant",
            "content": f"User: {query} | Assistant: {answer[:300]}...",
            "referenced_node_ids": referenced_node_ids,
        }

        if promoted_playbook:
            turn_payload["playbook"] = promoted_playbook

        return self.tools.sync_agent_memory(user_id=user_id, turn_data=turn_payload)

    def record_shared_playbook(self, playbook_data: Dict[str, Any]) -> None:
        """Promote a verified procedural playbook into the shared company_brain graph."""
        pb_id = playbook_data.get("id") or f"playbook-{int(time.time())}"
        target_sys = playbook_data.get("target_system") or "ml-inference-worker"
        cypher = """
        MERGE (p:Playbook {id: $pb_id})
        SET p.trigger_signature = $trigger,
            p.resolution_steps = $steps,
            p.verified_by_ticket_id = $ticket_id,
            p.target_system = $target_sys,
            p.success_count = coalesce(p.success_count, 0) + 1
        WITH p
        MATCH (s:System {id: $target_sys})
        MERGE (p)-[:APPLIES_TO]->(s)
        RETURN p
        """
        self.tools.company_graph.query(
            cypher,
            {
                "pb_id": pb_id,
                "trigger": playbook_data.get("trigger_signature", ""),
                "steps": playbook_data.get("resolution_steps", []),
                "ticket_id": playbook_data.get("verified_by_ticket_id", ""),
                "target_sys": target_sys,
            },
        )
