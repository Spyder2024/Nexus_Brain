"""Massive Synthetic Enterprise Dataset Generator for NexusBrain.

Simulates "7bit Cloud Technologies" - an AI/Cloud SaaS enterprise with 8 teams,
65 engineers, 24 microservices, 250 tickets, 400 pull requests, 180 slack threads,
90 documents, 60 architectural decisions (20 temporal chains), and ~4,000+ graph edges.

Deterministically seeded with 5 planted "Golden Demo Scenarios" for hackathon evaluations.
"""

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pydantic import BaseModel
from src.config import DATA_PROCESSED_DIR, DATA_RAW_DIR, ensure_directories, settings
from src.schema.models import (
    Decision,
    DecisionStatus,
    DocStatus,
    DocType,
    Document,
    GraphBundle,
    GraphEdge,
    NodeType,
    Person,
    PullRequest,
    RelationType,
    SlackMessage,
    SlackThread,
    System,
    SystemTier,
    Team,
    Ticket,
    TicketSeverity,
    TicketType,
)


class EnterpriseDataGenerator:
    """Deterministic, seed-controlled enterprise graph simulator for 7bit Cloud Technologies."""

    def __init__(self, seed: int = 42, base_date: Optional[datetime] = None):
        self.seed = seed
        self.rng = random.Random(seed)
        # Reference date set to October 2026
        self.base_date = base_date or datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Storage containers
        self.teams: List[Team] = []
        self.people: List[Person] = []
        self.systems: List[System] = []
        self.tickets: List[Ticket] = []
        self.pull_requests: List[PullRequest] = []
        self.slack_threads: List[SlackThread] = []
        self.documents: List[Document] = []
        self.decisions: List[Decision] = []
        self.edges: List[GraphEdge] = []

        # Index maps for fast cross-referencing
        self.people_by_id: Dict[str, Person] = {}
        self.people_by_team: Dict[str, List[Person]] = {}
        self.systems_by_id: Dict[str, System] = {}
        self.systems_by_owner: Dict[str, List[System]] = {}
        self.tickets_by_id: Dict[str, Ticket] = {}
        self.decisions_by_id: Dict[str, Decision] = {}

    def _rand_dt(self, start_days_ago: int, end_days_ago: int = 0) -> datetime:
        """Return a random datetime between start_days_ago and end_days_ago relative to base_date."""
        delta_days = self.rng.randint(min(start_days_ago, end_days_ago), max(start_days_ago, end_days_ago))
        delta_seconds = self.rng.randint(0, 86399)
        return self.base_date - timedelta(days=delta_days, seconds=delta_seconds)

    def _format_dt(self, dt: datetime) -> str:
        return dt.isoformat()

    def _add_edge(
        self,
        source_id: str,
        source_label: NodeType | str,
        target_id: str,
        target_label: NodeType | str,
        relation_type: RelationType | str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a validated directed edge in the enterprise graph."""
        s_lbl = source_label.value if isinstance(source_label, NodeType) else str(source_label)
        t_lbl = target_label.value if isinstance(target_label, NodeType) else str(target_label)
        r_typ = relation_type.value if isinstance(relation_type, RelationType) else str(relation_type)

        edge = GraphEdge(
            source_id=source_id,
            source_label=s_lbl,
            target_id=target_id,
            target_label=t_lbl,
            relation_type=r_typ,
            properties=properties or {},
        )
        self.edges.append(edge)

    # -------------------------------------------------------------------------
    # 1. Teams Generation (8 Teams)
    # -------------------------------------------------------------------------
    def _generate_teams(self) -> None:
        team_defs = [
            ("team-core-platform", "Core Platform", "Platform Engineering", "person-01", "#core-platform"),
            ("team-auth-identity", "Auth & Identity", "Security & Identity", "person-04", "#auth-identity"),
            ("team-payment-billing", "Payment & Billing", "Commerce & Revenue", "person-12", "#payment-billing"),
            ("team-ml-inference", "ML Inference Engine", "AI & Machine Learning", "person-20", "#ml-inference"),
            ("team-data-pipeline", "Data Pipeline", "Data Engineering", "person-28", "#data-pipeline"),
            ("team-sre-infra", "SRE & Cloud Infra", "Platform & Reliability", "person-36", "#sre-infra"),
            ("team-frontend-exp", "Frontend Experience", "Product Engineering", "person-44", "#frontend-exp"),
            ("team-security-compliance", "Security & Compliance", "InfoSec & Governance", "person-52", "#security-ops"),
        ]

        for team_id, name, dept, lead_id, slack in team_defs:
            team = Team(
                id=team_id,
                name=name,
                department=dept,
                lead_id=lead_id,
                slack_channel=slack,
            )
            self.teams.append(team)

    # -------------------------------------------------------------------------
    # 2. People Generation (65 Engineers & Staff)
    # -------------------------------------------------------------------------
    def _generate_people(self) -> None:
        first_names = [
            "Elena", "Liam", "Marcus", "Aria", "Devon", "Siddharth", "Chloe", "Zainab",
            "Kenji", "Priya", "Carlos", "Sophia", "Alexei", "Fatima", "Tobias", "Mei",
            "Julian", "Ananya", "Mateo", "Ingrid", "Vikram", "Tara", "Nathalie", "Dante",
            "Freja", "Kiran", "Lucas", "Yuki", "Omari", "Leila", "Dmitri", "Samira",
            "Ethan", "Mira", "Rafael", "Hana", "Arjun", "Valeria", "Nico", "Lin",
            "Gabriel", "Sunita", "Oliver", "Maya", "Henrik", "Noor", "Xavier", "Rhea",
            "Lars", "Amara", "Tariq", "Chiara", "Rowan", "Sora", "Dara", "Zubair",
            "Clara", "Kaelen", "Amina", "Einar", "Shreya", "Ezra", "Siobhan", "Farhan", "Yasmine"
        ]
        last_names = [
            "Rostova", "Chen", "Vance", "Alvarez", "Kim", "Patel", "Dubois", "Al-Mansoor",
            "Takahashi", "Sharma", "Mendoza", "Novak", "Volkov", "Haddad", "Lindqvist", "Zhang",
            "Moreau", "Iyer", "Silva", "Larsson", "Reddy", "O'Connor", "Boucher", "Costa",
            "Berg", "Deshmukh", "Santoro", "Sato", "Diallo", "Khoury", "Popov", "Jamil",
            "Brooks", "Nair", "Reyes", "Tanaka", "Choudhury", "Gomez", "Ricci", "Wu",
            "Fischer", "Gupta", "Gallagher", "Kapoor", "Nygard", "Bakhash", "Mercier", "Verma",
            "Jensen", "Eze", "Kassim", "Conti", "Adler", "Morita", "Connolly", "Rahman",
            "Sinclair", "Sinha", "Suleiman", "Holm", "Sen", "Sterling", "Kowalski", "Mirza", "Zhao"
        ]

        skills_pool = [
            "Go", "Rust", "Python", "TypeScript", "Distributed Systems", "Kubernetes",
            "Kafka", "Redis", "FalkorDB", "gRPC", "Docker", "PyTorch", "vLLM", "PostgreSQL",
            "AWS", "GraphQL", "React", "Terraform", "OpenTelemetry", "Security Auditing",
            "eBPF", "CUDA", "CI/CD", "Prometheus", "Citus Sharding"
        ]

        roles = [
            "Staff SRE", "Principal Architect", "Senior Backend Engineer", "Lead Security Engineer",
            "MLOps Engineer", "Data Infrastructure Engineer", "Senior Frontend Engineer",
            "Engineering Manager", "Backend Engineer", "Systems Engineer", "Cloud Reliability Engineer"
        ]
        seniority_levels = ["Principal", "Staff", "Senior", "Mid", "Junior"]

        # Ensure Person-19 is Elena Rostova (Staff SRE on team-sre-infra) for Golden Scenario 1
        # Ensure Person-04 is Liam Chen (Lead of team-auth-identity)
        team_ids = [t.id for t in self.teams]

        for i in range(1, 66):
            pid = f"person-{i:02d}"
            fn = first_names[(i - 1) % len(first_names)]
            ln = last_names[(i - 1) % len(last_names)]
            full_name = f"{fn} {ln}"

            # Golden scenario 1 anchored characters
            if i == 4:
                full_name = "Liam Chen"
                team_id = "team-auth-identity"
                role = "Lead Identity Architect"
                seniority = "Staff"
                skills = ["Go", "Distributed Systems", "OAuth2", "gRPC", "Redis", "Security Auditing"]
                joined_date = "2022-03-15"
            elif i == 19:
                full_name = "Elena Rostova"
                team_id = "team-sre-infra"
                role = "Staff Site Reliability Engineer"
                seniority = "Staff"
                skills = ["Go", "Kubernetes", "Redis", "eBPF", "Prometheus", "Distributed Systems", "gRPC"]
                joined_date = "2021-11-01"
            elif i == 1:
                full_name = "Marcus Vance"
                team_id = "team-core-platform"
                role = "Principal Platform Architect"
                seniority = "Principal"
                skills = ["Go", "Rust", "Distributed Systems", "Kafka", "FalkorDB", "Kubernetes"]
                joined_date = "2021-01-10"
            elif i == 20:
                full_name = "Devon Kim"
                team_id = "team-ml-inference"
                role = "Staff ML Systems Architect"
                seniority = "Staff"
                skills = ["Python", "PyTorch", "CUDA", "vLLM", "Docker", "Triton"]
                joined_date = "2022-07-01"
            else:
                # Distribute across teams evenly
                team_id = team_defs_index = team_ids[(i - 1) % len(team_ids)]
                role = self.rng.choice(roles)
                seniority = self.rng.choice(seniority_levels)
                skills = self.rng.sample(skills_pool, k=self.rng.randint(4, 7))
                joined_year = self.rng.randint(2021, 2025)
                joined_month = self.rng.randint(1, 12)
                joined_day = self.rng.randint(1, 28)
                joined_date = f"{joined_year}-{joined_month:02d}-{joined_day:02d}"

            person = Person(
                id=pid,
                name=full_name,
                role=role,
                seniority=seniority,
                team_id=team_id,
                skills=skills,
                joined_date=joined_date,
                active=True,
            )
            self.people.append(person)
            self.people_by_id[pid] = person
            self.people_by_team.setdefault(team_id, []).append(person)

            # Edge: MEMBER_OF
            self._add_edge(
                source_id=pid,
                source_label=NodeType.PERSON,
                target_id=team_id,
                target_label=NodeType.TEAM,
                relation_type=RelationType.MEMBER_OF,
                properties={"role": role, "since": joined_date},
            )

        # Edges: LEADS (Team Leads)
        for t in self.teams:
            self._add_edge(
                source_id=t.lead_id,
                source_label=NodeType.PERSON,
                target_id=t.id,
                target_label=NodeType.TEAM,
                relation_type=RelationType.LEADS,
                properties={"title": f"Lead of {t.name}"},
            )

    # -------------------------------------------------------------------------
    # 3. Systems Generation (24 Microservices & Core Infra)
    # -------------------------------------------------------------------------
    def _generate_systems(self) -> None:
        """Create 24 microservices with dependencies forming clear critical paths."""
        systems_def = [
            # Core & Auth (Tier-0)
            ("auth-service", "Authentication & Authorization Service", SystemTier.TIER_0, "Go", "team-auth-identity", "person-04"),
            ("redis-session-store", "Redis Session & Token Cache Cluster", SystemTier.TIER_0, "Rust", "team-core-platform", "person-01"),
            ("auth-token-validator", "Edge JWT & Session Token Validator", SystemTier.TIER_0, "Go", "team-auth-identity", "person-04"),
            ("kafka-event-bus", "Enterprise Kafka Distributed Bus", SystemTier.TIER_0, "Java", "team-core-platform", "person-01"),
            ("redis-state-cluster", "Distributed Distributed State Cache", SystemTier.TIER_0, "C", "team-core-platform", "person-02"),
            ("vector-gateway", "Vector Search & FalkorDB Graph Gateway", SystemTier.TIER_1, "Python", "team-core-platform", "person-03"),

            # Payment & Commerce (Tier-1)
            ("billing-ledger", "Double-Entry Ledger & Invoicing Engine", SystemTier.TIER_0, "Go", "team-payment-billing", "person-12"),
            ("checkout-orchestrator", "Checkout Workflow & Order Coordinator", SystemTier.TIER_1, "Go", "team-payment-billing", "person-13"),
            ("stripe-webhook-worker", "Stripe Event Ingestion & Webhook Processor", SystemTier.TIER_1, "TypeScript", "team-payment-billing", "person-14"),

            # User & Product
            ("user-profile-service", "User Profile & Organization Directory", SystemTier.TIER_1, "Go", "team-core-platform", "person-05"),
            ("recommendation-service", "Personalized User Recommendation Engine", SystemTier.TIER_2, "Python", "team-ml-inference", "person-21"),

            # ML & AI
            ("ml-inference-worker", "Distributed PyTorch Model Inference Worker", SystemTier.TIER_1, "Python", "team-ml-inference", "person-20"),
            ("model-registry-service", "Weights & Versioned Artifact Registry", SystemTier.TIER_2, "Python", "team-ml-inference", "person-22"),
            ("feature-store-api", "Real-time Low-Latency Feature Store", SystemTier.TIER_1, "Go", "team-ml-inference", "person-23"),

            # Data Pipeline
            ("data-lakehouse-ingest", "High-Throughput Lakehouse Ingestion Engine", SystemTier.TIER_2, "Scala", "team-data-pipeline", "person-28"),
            ("event-stream-enricher", "Streaming Flink Event Enricher", SystemTier.TIER_1, "Java", "team-data-pipeline", "person-29"),
            ("metrics-aggregation-pipeline", "Timeseries Telemetry Aggregator", SystemTier.TIER_2, "Go", "team-data-pipeline", "person-30"),

            # Frontend & Web
            ("frontend-bff-gateway", "Backend-For-Frontend GraphQL Gateway", SystemTier.TIER_1, "TypeScript", "team-frontend-exp", "person-44"),
            ("web-client-spa", "Next.js Web Enterprise Console", SystemTier.TIER_2, "TypeScript", "team-frontend-exp", "person-45"),
            ("admin-console-service", "Internal Operational Backoffice API", SystemTier.TIER_3, "Go", "team-frontend-exp", "person-46"),

            # SRE & Security Infra
            ("audit-log-vault", "Immutable Security Audit Ledger", SystemTier.TIER_1, "Rust", "team-security-compliance", "person-52"),
            ("secrets-kms-proxy", "Vault & KMS Encryption Proxy", SystemTier.TIER_0, "Go", "team-security-compliance", "person-53"),
            ("network-mesh-ingress", "Envoy Global Ingress & API Gateway", SystemTier.TIER_0, "C++", "team-sre-infra", "person-36"),
            ("cloud-cost-optimizer", "Spot Instance & Autoscaling Controller", SystemTier.TIER_3, "Python", "team-sre-infra", "person-37"),
        ]

        for sid, name, tier, lang, owner_team, maintainer_id in systems_def:
            sys_obj = System(
                id=sid,
                name=name,
                tier=tier.value,
                language=lang,
                repo_url=f"https://github.com/7bitcloud/{sid}",
                owner_team_id=owner_team,
                primary_maintainer_id=maintainer_id,
            )
            self.systems.append(sys_obj)
            self.systems_by_id[sid] = sys_obj
            self.systems_by_owner.setdefault(owner_team, []).append(sys_obj)

            # Edge: OWNS (Team -> System)
            self._add_edge(
                source_id=owner_team,
                source_label=NodeType.TEAM,
                target_id=sid,
                target_label=NodeType.SYSTEM,
                relation_type=RelationType.OWNS,
                properties={"tier": tier.value},
            )

            # Edge: MAINTAINS (Person -> System)
            self._add_edge(
                source_id=maintainer_id,
                source_label=NodeType.PERSON,
                target_id=sid,
                target_label=NodeType.SYSTEM,
                relation_type=RelationType.MAINTAINS,
                properties={"primary": True},
            )

        # ---------------------------------------------------------------------
        # Directed Dependencies (DEPENDS_ON)
        # Note: Golden Scenario 3:
        # stripe-webhook-worker -> checkout-orchestrator -> auth-token-validator -> redis-session-store
        # Note: Golden Scenario 5:
        # recommendation-service -> user-profile-service
        # ---------------------------------------------------------------------
        explicit_deps = [
            # Golden Scenario 3 Chain (4-hop cascading blast radius across 3 teams)
            ("stripe-webhook-worker", "checkout-orchestrator"),
            ("checkout-orchestrator", "auth-token-validator"),
            ("auth-token-validator", "redis-session-store"),

            # Golden Scenario 5 Chain
            ("recommendation-service", "user-profile-service"),
            ("recommendation-service", "feature-store-api"),

            # Core infrastructure dependencies
            ("auth-service", "redis-session-store"),
            ("auth-service", "secrets-kms-proxy"),
            ("auth-token-validator", "secrets-kms-proxy"),
            ("checkout-orchestrator", "billing-ledger"),
            ("checkout-orchestrator", "kafka-event-bus"),
            ("billing-ledger", "audit-log-vault"),
            ("user-profile-service", "auth-token-validator"),
            ("user-profile-service", "redis-state-cluster"),
            ("frontend-bff-gateway", "auth-token-validator"),
            ("frontend-bff-gateway", "user-profile-service"),
            ("frontend-bff-gateway", "checkout-orchestrator"),
            ("web-client-spa", "frontend-bff-gateway"),
            ("admin-console-service", "audit-log-vault"),
            ("admin-console-service", "auth-service"),
            ("ml-inference-worker", "model-registry-service"),
            ("ml-inference-worker", "vector-gateway"),
            ("ml-inference-worker", "redis-state-cluster"),
            ("feature-store-api", "redis-state-cluster"),
            ("feature-store-api", "kafka-event-bus"),
            ("data-lakehouse-ingest", "kafka-event-bus"),
            ("event-stream-enricher", "kafka-event-bus"),
            ("event-stream-enricher", "user-profile-service"),
            ("metrics-aggregation-pipeline", "kafka-event-bus"),
            ("network-mesh-ingress", "auth-token-validator"),
            ("network-mesh-ingress", "frontend-bff-gateway"),
            ("cloud-cost-optimizer", "metrics-aggregation-pipeline"),
            ("audit-log-vault", "secrets-kms-proxy"),
        ]

        for source_sys, target_sys in explicit_deps:
            self._add_edge(
                source_id=source_sys,
                source_label=NodeType.SYSTEM,
                target_id=target_sys,
                target_label=NodeType.SYSTEM,
                relation_type=RelationType.DEPENDS_ON,
                properties={"protocol": "gRPC" if "service" in target_sys else "TCP/Driver"},
            )

    # -------------------------------------------------------------------------
    # 4. Tickets Generation (250 Tickets & Incidents)
    # -------------------------------------------------------------------------
    def _generate_tickets(self) -> None:
        """Generate 250 tickets including incidents, bugs, features, and tech debt."""

        # ---------------------------------------------------------------------
        # Plant Golden Scenarios Tickets
        # ---------------------------------------------------------------------

        # Scenario 1: Person-19 resolving 18 SEV-1 tickets on auth-service over the last 60 days
        for i in range(1, 19):
            ticket_id = f"INC-AUTH-{i:03d}"
            created_dt = self._rand_dt(start_days_ago=58, end_days_ago=2)
            resolved_dt = created_dt + timedelta(minutes=self.rng.randint(35, 180))
            reporter = self.rng.choice([p.id for p in self.people if p.team_id == "team-auth-identity" or p.id == "person-04"])

            ticket = Ticket(
                id=ticket_id,
                title=f"Critical auth-service connection pool saturation & latency spike #{i}",
                type=TicketType.INCIDENT.value,
                severity=TicketSeverity.SEV_1.value,
                status="resolved",
                created_at=self._format_dt(created_dt),
                resolved_at=self._format_dt(resolved_dt),
                reporter_id=reporter,
                assignee_id="person-19",  # Elena Rostova (SRE)
                affected_system_id="auth-service",
                root_cause_system_id="redis-session-store" if i % 2 == 0 else "auth-service",
                summary=(
                    f"SEV-1 Incident on auth-service: gRPC thread pool exhaustion under heavy traffic. "
                    f"Mitigated and resolved by Elena Rostova (person-19) via dynamic pool tuning and TCP keepalive patches."
                ),
            )
            self.tickets.append(ticket)
            self.tickets_by_id[ticket_id] = ticket

        # Scenario 2 Ticket: INC-204 (The deadlock that triggered ADR-051)
        inc_204_dt = self.base_date - timedelta(days=24)
        inc_204_res = inc_204_dt + timedelta(hours=3, minutes=45)
        ticket_inc_204 = Ticket(
            id="INC-204",
            title="Production Deadlock: Synchronous Kafka RPC consumer lag blocking checkout authorizations",
            type=TicketType.INCIDENT.value,
            severity=TicketSeverity.SEV_1.value,
            status="resolved",
            created_at=self._format_dt(inc_204_dt),
            resolved_at=self._format_dt(inc_204_res),
            reporter_id="person-12",  # Payment lead
            assignee_id="person-01",  # Core platform lead
            affected_system_id="checkout-orchestrator",
            root_cause_system_id="kafka-event-bus",
            summary=(
                "Synchronous request-response pattern implemented on Kafka topics deadlocked when consumer rebalances "
                "stalled payment authorization reply partitions. Direct catalyst for ADR-051 and deprecation of synchronous Kafka RPC."
            ),
        )
        self.tickets.append(ticket_inc_204)
        self.tickets_by_id[ticket_inc_204.id] = ticket_inc_204

        # Scenario 3 Ticket: INC-119 (4-hop cascading blast radius)
        inc_119_dt = self.base_date - timedelta(days=75)
        inc_119_res = inc_119_dt + timedelta(hours=2, minutes=10)
        ticket_inc_119 = Ticket(
            id="INC-119",
            title="Cascading Checkout Outage: Redis session cluster OOM eviction propagating to payment webhooks",
            type=TicketType.INCIDENT.value,
            severity=TicketSeverity.SEV_1.value,
            status="resolved",
            created_at=self._format_dt(inc_119_dt),
            resolved_at=self._format_dt(inc_119_res),
            reporter_id="person-14",  # Webhook maintainer
            assignee_id="person-19",  # Elena Rostova
            affected_system_id="stripe-webhook-worker",
            root_cause_system_id="redis-session-store",
            summary=(
                "Catastrophic 4-hop cascading failure: redis-session-store memory eviction triggered 504 Gateway Timeouts "
                "in auth-token-validator, causing checkout-orchestrator backpressure, and halting stripe-webhook-worker."
            ),
        )
        self.tickets.append(ticket_inc_119)
        self.tickets_by_id[ticket_inc_119.id] = ticket_inc_119

        # Scenario 4 Tickets: INC-045 (4 months ago) and INC-249 (2 days ago)
        inc_045_dt = self.base_date - timedelta(days=120)
        inc_045_res = inc_045_dt + timedelta(hours=4)
        ticket_inc_045 = Ticket(
            id="INC-045",
            title="ML Inference Worker CUDA Memory Leak & OOM Killer crash under batch tensor load",
            type=TicketType.INCIDENT.value,
            severity=TicketSeverity.SEV_1.value,
            status="resolved",
            created_at=self._format_dt(inc_045_dt),
            resolved_at=self._format_dt(inc_045_res),
            reporter_id="person-21",
            assignee_id="person-20",  # Devon Kim
            affected_system_id="ml-inference-worker",
            root_cause_system_id="ml-inference-worker",
            summary=(
                "PyTorch worker nodes encountering CUDA memory fragmentation and uncollected tensor graphs after 72h runtime. "
                "Mitigation documented in DOC-012."
            ),
        )
        self.tickets.append(ticket_inc_045)
        self.tickets_by_id[ticket_inc_045.id] = ticket_inc_045

        inc_249_dt = self.base_date - timedelta(days=2)
        ticket_inc_249 = Ticket(
            id="INC-249",
            title="ML Inference Worker CUDA Memory Leak Resurfaces: Worker nodes OOM killed on GPU shard 4",
            type=TicketType.INCIDENT.value,
            severity=TicketSeverity.SEV_1.value,
            status="in_progress",
            created_at=self._format_dt(inc_249_dt),
            resolved_at=None,
            reporter_id="person-22",
            assignee_id="person-20",  # Devon Kim
            affected_system_id="ml-inference-worker",
            root_cause_system_id="ml-inference-worker",
            summary=(
                "Exact recurrence of INC-045: PyTorch worker nodes experiencing CUDA memory leak and OOM crash under batched tensor inference. "
                "Requires DOC-012 procedure."
            ),
        )
        self.tickets.append(ticket_inc_249)
        self.tickets_by_id[ticket_inc_249.id] = ticket_inc_249

        # Scenario 5 Ticket: INC-250 (Breaking schema change)
        inc_250_dt = self.base_date - timedelta(days=1)
        ticket_inc_250 = Ticket(
            id="INC-250",
            title="Recommendation Engine Unmarshaling Panic: Missing required field 'account_tier' in User Profile payload",
            type=TicketType.INCIDENT.value,
            severity=TicketSeverity.SEV_2.value,
            status="open",
            created_at=self._format_dt(inc_250_dt),
            resolved_at=None,
            reporter_id="person-21",  # Recommendation maintainer
            assignee_id="person-05",  # User profile author
            affected_system_id="recommendation-service",
            root_cause_system_id="user-profile-service",
            summary=(
                "recommendation-service panics when consuming user profiles following PR-398 breaking schema modification. "
                "Field account_tier was removed without backward compatibility."
            ),
        )
        self.tickets.append(ticket_inc_250)
        self.tickets_by_id[ticket_inc_250.id] = ticket_inc_250

        # ---------------------------------------------------------------------
        # Remaining General Realistic Tickets (filling up to 250)
        # ---------------------------------------------------------------------
        incident_topics = [
            ("Database connection pool starvation during flash sale traffic", TicketType.INCIDENT, TicketSeverity.SEV_2),
            ("Kafka consumer rebalance loop causing event lag in streaming enricher", TicketType.INCIDENT, TicketSeverity.SEV_2),
            ("gRPC deadline exceeded between checkout-orchestrator and billing-ledger", TicketType.INCIDENT, TicketSeverity.SEV_2),
            ("Stale read replicas returning outdated user organization metadata", TicketType.BUG, TicketSeverity.SEV_3),
            ("TLS certificate rotation failure on internal network mesh ingress", TicketType.INCIDENT, TicketSeverity.SEV_1),
            ("Frontend BFF memory leak on unclosed GraphQL subscriptions", TicketType.BUG, TicketSeverity.SEV_3),
            ("Vector gateway FalkorDB Cypher timeout on multi-hop graph queries", TicketType.BUG, TicketSeverity.SEV_3),
            ("Audit log vault disk threshold alert in EU-Central availability zone", TicketType.INCIDENT, TicketSeverity.SEV_2),
            ("Migrate billing-ledger balance calculations to decimal precision library", TicketType.TECH_DEBT, TicketSeverity.SEV_4),
            ("Implement distributed rate limiting on public OpenAPI endpoints", TicketType.FEATURE, TicketSeverity.SEV_3),
            ("Decommission legacy v1 user authentication endpoints", TicketType.TECH_DEBT, TicketSeverity.SEV_4),
            ("Add OpenTelemetry distributed tracing context propagation to Redis clients", TicketType.FEATURE, TicketSeverity.SEV_3),
            ("Investigate intermittent 502 Bad Gateway from web-client-spa to BFF", TicketType.BUG, TicketSeverity.SEV_3),
            ("Automate spot instance eviction drain handlers in cloud-cost-optimizer", TicketType.FEATURE, TicketSeverity.SEV_4),
            ("Lakehouse ingest S3 multipart upload timeout during peak batch window", TicketType.BUG, TicketSeverity.SEV_3),
        ]

        current_count = len(self.tickets)
        needed = 250 - current_count

        for i in range(1, needed + 1):
            tid = f"TICKET-{i + 100:03d}"
            title_tpl, t_type, t_sev = self.rng.choice(incident_topics)
            target_sys = self.rng.choice(self.systems)
            root_sys = self.rng.choice([target_sys, self.rng.choice(self.systems)])

            created_dt = self._rand_dt(start_days_ago=365, end_days_ago=1)
            is_resolved = self.rng.random() > 0.15
            resolved_dt = created_dt + timedelta(hours=self.rng.randint(1, 72)) if is_resolved else None

            # Pick reporter and assignee from related teams
            reporter = self.rng.choice(self.people).id
            assignee = self.rng.choice(self.people).id

            ticket = Ticket(
                id=tid,
                title=f"{title_tpl} ({target_sys.id})",
                type=t_type.value,
                severity=t_sev.value,
                status="resolved" if is_resolved else "in_progress",
                created_at=self._format_dt(created_dt),
                resolved_at=self._format_dt(resolved_dt) if resolved_dt else None,
                reporter_id=reporter,
                assignee_id=assignee,
                affected_system_id=target_sys.id,
                root_cause_system_id=root_sys.id if t_type == TicketType.INCIDENT else None,
                summary=f"Technical incident/task {tid} affecting {target_sys.id}. Status: {'Resolved' if is_resolved else 'Active'}.",
            )
            self.tickets.append(ticket)
            self.tickets_by_id[tid] = ticket

        # Create Edges for all Tickets
        for t in self.tickets:
            # REPORTED (Person -> Ticket)
            self._add_edge(
                source_id=t.reporter_id,
                source_label=NodeType.PERSON,
                target_id=t.id,
                target_label=NodeType.TICKET,
                relation_type=RelationType.REPORTED,
                properties={"created_at": t.created_at},
            )
            # ASSIGNED_TO (Ticket -> Person)
            self._add_edge(
                source_id=t.id,
                source_label=NodeType.TICKET,
                target_id=t.assignee_id,
                target_label=NodeType.PERSON,
                relation_type=RelationType.ASSIGNED_TO,
                properties={"status": t.status},
            )
            # AFFECTS (Ticket -> System)
            self._add_edge(
                source_id=t.id,
                source_label=NodeType.TICKET,
                target_id=t.affected_system_id,
                target_label=NodeType.SYSTEM,
                relation_type=RelationType.AFFECTS,
                properties={"severity": t.severity},
            )
            # CAUSED_BY (Ticket -> System)
            if t.root_cause_system_id:
                self._add_edge(
                    source_id=t.id,
                    source_label=NodeType.TICKET,
                    target_id=t.root_cause_system_id,
                    target_label=NodeType.SYSTEM,
                    relation_type=RelationType.CAUSED_BY,
                    properties={"severity": t.severity},
                )

    # -------------------------------------------------------------------------
    # 5. Pull Requests Generation (400 PRs)
    # -------------------------------------------------------------------------
    def _generate_pull_requests(self) -> None:
        """Generate 400 PRs linked to tickets, systems, authors, and reviewers."""

        # ---------------------------------------------------------------------
        # Plant Golden Scenario 1 PRs:
        # Person-19 authored 25 PRs on auth-service over the last 60 days
        # ---------------------------------------------------------------------
        for i in range(1, 26):
            pr_id = f"PR-AUTH-{i:03d}"
            pr_dt = self._rand_dt(start_days_ago=58, end_days_ago=2)
            reviewers = self.rng.sample([p.id for p in self.people if p.id != "person-19"], k=2)

            pr = PullRequest(
                id=pr_id,
                title=f"fix(auth-service): Optimize connection pooling and TCP keepalive #{i}",
                author_id="person-19",  # Elena Rostova
                reviewer_ids=reviewers,
                system_id="auth-service",
                linked_ticket_id=f"INC-AUTH-{(i % 18) + 1:03d}",
                merged_at=self._format_dt(pr_dt + timedelta(hours=self.rng.randint(2, 12))),
                files_changed=["internal/pool/conn.go", "config/tuning.yaml", "cmd/server/main.go"],
                commit_summary=f"Tuned gRPC transport and max connection buffers on auth-service to prevent exhaustion under SEV-1 traffic.",
            )
            self.pull_requests.append(pr)

        # ---------------------------------------------------------------------
        # Plant Golden Scenario 5 PR:
        # PR-398: Merged yesterday, modifies user-profile-service without updating recommendation-service
        # ---------------------------------------------------------------------
        pr_398_dt = self.base_date - timedelta(days=1, hours=8)
        pr_398 = PullRequest(
            id="PR-398",
            title="refactor(user-profile): Migrate to subscription_v2 schema and prune deprecated account_tier field",
            author_id="person-05",  # Core platform engineer
            reviewer_ids=["person-01", "person-04"],
            system_id="user-profile-service",
            linked_ticket_id="TICKET-110",
            merged_at=self._format_dt(pr_398_dt),
            files_changed=[
                "api/proto/user_profile.proto",
                "services/profile/v2/serializer.go",
                "schemas/user_profile.json",
            ],
            commit_summary=(
                "Removed legacy account_tier string field from user profile protobuf and JSON serializers. "
                "Downstream services must consume subscription_v2.tier enum."
            ),
        )
        self.pull_requests.append(pr_398)

        # ---------------------------------------------------------------------
        # Remaining General PRs (filling up to 400)
        # ---------------------------------------------------------------------
        needed = 400 - len(self.pull_requests)
        file_templates = [
            ("internal/transport/grpc_server.go", "api/v1/service.proto"),
            ("pkg/database/migrations/004_index.sql", "pkg/database/client.go"),
            ("src/components/Dashboard/MetricsView.tsx", "src/hooks/useMetrics.ts"),
            ("config/helm/values-prod.yaml", "Dockerfile"),
            ("workers/pipeline/batch_processor.py", "tests/test_pipeline.py"),
            ("infra/terraform/modules/rds/main.tf", "infra/terraform/outputs.tf"),
            ("models/transformer/inference_engine.py", "models/transformer/utils.py"),
            ("pkg/auth/token_verifier.go", "pkg/auth/jwks_cache.go"),
        ]

        pr_titles = [
            "feat({sys}): Implement distributed tracing and SpanContext propagation",
            "fix({sys}): Handle graceful shutdown on SIGTERM and flush buffer",
            "perf({sys}): Add L1 in-memory cache with LRU eviction policy",
            "refactor({sys}): Extract validation logic into standalone reusable package",
            "chore({sys}): Bump dependencies and resolve CVE security vulnerabilities",
            "fix({sys}): Prevent race condition in concurrent map write",
            "feat({sys}): Add Prometheus histogram metrics for p99 latency monitoring",
            "test({sys}): Increase end-to-end integration test coverage to 85%",
        ]

        for i in range(1, needed + 1):
            pr_num = i + 26
            pr_id = f"PR-{pr_num:03d}"
            target_sys = self.rng.choice(self.systems)
            author = self.rng.choice(self.people).id
            candidate_reviewers = [p.id for p in self.people if p.id != author]
            reviewers = self.rng.sample(candidate_reviewers, k=2)

            title_tpl = self.rng.choice(pr_titles)
            title = title_tpl.format(sys=target_sys.id)

            pr_dt = self._rand_dt(start_days_ago=360, end_days_ago=2)
            merged_dt = pr_dt + timedelta(hours=self.rng.randint(2, 48))

            # Sample changed files
            base_files = list(self.rng.choice(file_templates))

            # Link to a ticket ~70% of the time
            linked_t = self.rng.choice(self.tickets).id if self.rng.random() > 0.3 else None

            pr = PullRequest(
                id=pr_id,
                title=title,
                author_id=author,
                reviewer_ids=reviewers,
                system_id=target_sys.id,
                linked_ticket_id=linked_t,
                merged_at=self._format_dt(merged_dt),
                files_changed=base_files,
                commit_summary=f"Automated engineering enhancement on {target_sys.id}: {title}.",
            )
            self.pull_requests.append(pr)

        # Create Edges for all PullRequests
        for pr in self.pull_requests:
            # AUTHORED (Person -> PR)
            self._add_edge(
                source_id=pr.author_id,
                source_label=NodeType.PERSON,
                target_id=pr.id,
                target_label=NodeType.PULL_REQUEST,
                relation_type=RelationType.AUTHORED,
                properties={"merged_at": pr.merged_at},
            )
            # REVIEWED (Person -> PR)
            for rev_id in pr.reviewer_ids:
                self._add_edge(
                    source_id=rev_id,
                    source_label=NodeType.PERSON,
                    target_id=pr.id,
                    target_label=NodeType.PULL_REQUEST,
                    relation_type=RelationType.REVIEWED,
                    properties={"status": "approved"},
                )
            # MODIFIES (PR -> System)
            self._add_edge(
                source_id=pr.id,
                source_label=NodeType.PULL_REQUEST,
                target_id=pr.system_id,
                target_label=NodeType.SYSTEM,
                relation_type=RelationType.MODIFIES,
                properties={"file_count": len(pr.files_changed)},
            )
            # IMPLEMENTS / RESOLVES (PR -> Ticket)
            if pr.linked_ticket_id:
                rel = RelationType.RESOLVES if "fix" in pr.title.lower() or "INC" in pr.linked_ticket_id else RelationType.IMPLEMENTS
                self._add_edge(
                    source_id=pr.id,
                    source_label=NodeType.PULL_REQUEST,
                    target_id=pr.linked_ticket_id,
                    target_label=NodeType.TICKET,
                    relation_type=rel,
                    properties={"merged_at": pr.merged_at},
                )

    # -------------------------------------------------------------------------
    # 6. Slack Threads Generation (180 Threads)
    # -------------------------------------------------------------------------
    def _generate_slack_threads(self) -> None:
        """Generate 180 multi-turn discussion threads."""

        # ---------------------------------------------------------------------
        # Plant Golden Scenario 2 Thread:
        # SLACK-088: In #arch-sync debating INC-204 and agreeing to ADR-051
        # ---------------------------------------------------------------------
        t_088_dt = self.base_date - timedelta(days=22)
        slack_088 = SlackThread(
            id="SLACK-088",
            channel="#arch-sync",
            started_at=self._format_dt(t_088_dt),
            participant_ids=["person-01", "person-04", "person-12", "person-19", "person-36"],
            linked_ticket_id="INC-204",
            linked_decision_id="ADR-051",
            messages=[
                SlackMessage(
                    sender_id="person-12",
                    timestamp=self._format_dt(t_088_dt),
                    text="Team, INC-204 was unacceptable. We had checkout authorization hanging for 45 minutes because Kafka consumer partition rebalance paused replies.",
                ),
                SlackMessage(
                    sender_id="person-01",
                    timestamp=self._format_dt(t_088_dt + timedelta(minutes=6)),
                    text="Agreed Marcus. ADR-018 originally prescribed Kafka for RPC back in 2023, but at our current 85,000 req/sec scale, async RPC emulation over message queues creates unbounded tail latencies.",
                ),
                SlackMessage(
                    sender_id="person-19",
                    timestamp=self._format_dt(t_088_dt + timedelta(minutes=14)),
                    text="From SRE vantage: when broker rebalance triggers, timeouts cascade to upstream proxies. We must move synchronous inter-service calls directly to gRPC with HTTP/2 and mTLS.",
                ),
                SlackMessage(
                    sender_id="person-04",
                    timestamp=self._format_dt(t_088_dt + timedelta(minutes=22)),
                    text="Identity team supports this. We have protobuf specs ready. I will draft ADR-051 to officially deprecate sync Kafka RPC and supersede ADR-018 immediately.",
                ),
                SlackMessage(
                    sender_id="person-01",
                    timestamp=self._format_dt(t_088_dt + timedelta(minutes=30)),
                    text="Consensus reached. Let's record ADR-051 and update all service runbooks. Note: Ensure onboarding docs get updated so newcomers stop using Kafka for sync queries!",
                ),
            ],
        )
        self.slack_threads.append(slack_088)

        # ---------------------------------------------------------------------
        # Remaining General Slack Threads (filling up to 180)
        # ---------------------------------------------------------------------
        needed = 180 - len(self.slack_threads)
        channels = [
            "#incident-war-room", "#core-platform", "#arch-sync", "#infra-ops",
            "#auth-identity", "#ml-inference", "#data-pipeline", "#security-ops"
        ]

        chat_scenarios = [
            (
                "Redis memory eviction policy debate",
                "We are seeing `allkeys-lru` evict persistent session tokens under pressure. Should we move to `volatile-lru` with separate cluster?",
                "Yes, let's isolate cache from persistent state to avoid unannounced logouts.",
            ),
            (
                "Database connection pool starvation post-deploy",
                "Did anyone notice pgBouncer connection count hitting max on primary cluster?",
                "Investigating now. Looks like the new async batch worker didn't close connections properly in defer.",
            ),
            (
                "Vector search query latency SLA breach",
                "FalkorDB / vector hybrid queries are exceeding our 15ms target on multi-hop traversals.",
                "We need to add index hints on relation type and avoid unbound variable length paths.",
            ),
            (
                "Kubernetes pod eviction on node memory pressure",
                "Worker node ip-10-0-4-12 threw memory pressure taint. Two inference pods evicted.",
                "Karpenter is already spinning up an extra m6i.4xlarge instance. Traffic rerouted.",
            ),
        ]

        for i in range(1, needed + 1):
            s_num = i + 1 if i < 88 else i + 2
            sid = f"SLACK-{s_num:03d}"
            channel = self.rng.choice(channels)
            participants = self.rng.sample([p.id for p in self.people], k=self.rng.randint(3, 5))
            topic, msg1, msg2 = self.rng.choice(chat_scenarios)
            t_dt = self._rand_dt(start_days_ago=350, end_days_ago=1)

            # Optional linked ticket
            linked_t = self.rng.choice(self.tickets).id if self.rng.random() > 0.4 else None

            thread = SlackThread(
                id=sid,
                channel=channel,
                started_at=self._format_dt(t_dt),
                participant_ids=participants,
                linked_ticket_id=linked_t,
                linked_decision_id=None,
                messages=[
                    SlackMessage(
                        sender_id=participants[0],
                        timestamp=self._format_dt(t_dt),
                        text=f"[{topic}] {msg1}",
                    ),
                    SlackMessage(
                        sender_id=participants[1],
                        timestamp=self._format_dt(t_dt + timedelta(minutes=self.rng.randint(2, 10))),
                        text=msg2,
                    ),
                    SlackMessage(
                        sender_id=participants[2],
                        timestamp=self._format_dt(t_dt + timedelta(minutes=self.rng.randint(11, 25))),
                        text="Acknowledged. Changes verified in staging and metrics looking clean.",
                    ),
                ],
            )
            self.slack_threads.append(thread)

        # Create Edges for all SlackThreads
        for st in self.slack_threads:
            # PARTICIPATED_IN (Person -> SlackThread)
            for p_id in st.participant_ids:
                self._add_edge(
                    source_id=p_id,
                    source_label=NodeType.PERSON,
                    target_id=st.id,
                    target_label=NodeType.SLACK_THREAD,
                    relation_type=RelationType.PARTICIPATED_IN,
                    properties={"channel": st.channel},
                )
            # DISCUSSES (SlackThread -> Ticket)
            if st.linked_ticket_id:
                self._add_edge(
                    source_id=st.id,
                    source_label=NodeType.SLACK_THREAD,
                    target_id=st.linked_ticket_id,
                    target_label=NodeType.TICKET,
                    relation_type=RelationType.DISCUSSES,
                    properties={"channel": st.channel},
                )
            # TRIGGERED_DECISION (SlackThread -> Decision)
            if st.linked_decision_id:
                self._add_edge(
                    source_id=st.id,
                    source_label=NodeType.SLACK_THREAD,
                    target_id=st.linked_decision_id,
                    target_label=NodeType.DECISION,
                    relation_type=RelationType.TRIGGERED_DECISION,
                    properties={"channel": st.channel},
                )

    # -------------------------------------------------------------------------
    # 7. Technical Documents & Runbooks (90 Documents)
    # -------------------------------------------------------------------------
    def _generate_documents(self) -> None:
        """Generate 90 documents including Runbooks, RFCs, Postmortems, and Onboarding Guides."""

        # ---------------------------------------------------------------------
        # Plant Golden Scenario 2 Document:
        # Outdated Onboarding Document DOC-082 contradicting ADR-051
        # ---------------------------------------------------------------------
        doc_082_dt = self.base_date - timedelta(days=220)
        doc_082 = Document(
            id="DOC-082",
            title="Engineering Onboarding: Inter-Service Communication and Async RPC via Kafka",
            doc_type=DocType.ONBOARDING.value,
            author_id="person-01",  # Marcus Vance
            system_id="kafka-event-bus",
            last_updated=self._format_dt(doc_082_dt),
            status=DocStatus.OUTDATED.value,
            content=(
                "# Service Communication Standards (Deprecated)\n\n"
                "All microservices within 7bit Cloud Technologies MUST use Kafka for synchronous request-response communication. "
                "Publish requests to `<service>.requests` topic and subscribe to correlation UUIDs on `<service>.replies`.\n\n"
                "WARNING: This document is OUTDATED and CONTRADICTS ADR-051! "
                "Do not use Kafka for synchronous RPC; use gRPC over HTTP/2."
            ),
        )
        self.documents.append(doc_082)

        # ---------------------------------------------------------------------
        # Plant Golden Scenario 4 Document:
        # DOC-012: The Runbook that resolved INC-045 and guides resolution of INC-249
        # ---------------------------------------------------------------------
        doc_012_dt = self.base_date - timedelta(days=118)
        doc_012 = Document(
            id="DOC-012",
            title="Runbook: ML Inference Worker PyTorch CUDA Memory Leak Mitigation & Shard Recycling",
            doc_type=DocType.RUNBOOK.value,
            author_id="person-20",  # Devon Kim
            system_id="ml-inference-worker",
            last_updated=self._format_dt(doc_012_dt),
            status=DocStatus.ACTIVE.value,
            content=(
                "# ML Inference Worker CUDA OOM Triage Runbook\n\n"
                "## Symptoms:\n"
                "- PyTorch worker nodes experiencing CUDA memory fragmentation and uncollected tensor graphs after 72h runtime.\n"
                "- Linux kernel OOM Killer terminating process `torch_worker` with ExitCode 137 on GPU shard 4.\n\n"
                "## Resolution Steps:\n"
                "1. Trigger rolling pod restart with command: `kubectl rollout restart deployment/ml-inference-worker -n ml-prod`.\n"
                "2. Force CUDA cache deallocation via admin probe: `curl -X POST http://localhost:8080/admin/cuda/empty_cache`.\n"
                "3. Verify tensor shard memory stabilizes under 14GB on Grafana dashboard #402.\n"
                "4. Check historical incident reference: INC-045 and active recurrence INC-249."
            ),
        )
        self.documents.append(doc_012)

        # ---------------------------------------------------------------------
        # Remaining General Documents (filling up to 90)
        # ---------------------------------------------------------------------
        needed = 90 - len(self.documents)
        doc_templates = [
            ("Runbook: Redis Cluster Failover & Replication Resync", DocType.RUNBOOK, "redis-session-store"),
            ("Postmortem: INC-119 Cascading Checkout Outage Root Cause Analysis", DocType.POSTMORTEM, "checkout-orchestrator"),
            ("RFC-034: FalkorDB GraphRAG Knowledge Layer Integration Architecture", DocType.RFC, "vector-gateway"),
            ("Runbook: Emergency Auth Token Revocation & JWKS Key Rotation", DocType.RUNBOOK, "auth-token-validator"),
            ("Onboarding: Platform Engineering Guidelines and Local Dev Environment", DocType.ONBOARDING, "network-mesh-ingress"),
            ("Postmortem: INC-204 Kafka Consumer Partition Lag Deadlock", DocType.POSTMORTEM, "kafka-event-bus"),
            ("Runbook: Stripe Webhook Signature Verification and Dead-Letter Replay", DocType.RUNBOOK, "stripe-webhook-worker"),
            ("RFC-048: Zero-Trust mTLS with SPIFFE/SPIRE Identity Provisioning", DocType.RFC, "secrets-kms-proxy"),
            ("Runbook: Lakehouse Ingest Pipeline Backpressure and S3 Rate Limiting", DocType.RUNBOOK, "data-lakehouse-ingest"),
            ("RFC-052: Micro-frontend Architecture for Enterprise Web Console", DocType.RFC, "web-client-spa"),
        ]

        for i in range(1, needed + 1):
            d_num = i + 12 if i < 82 else i + 13
            did = f"DOC-{d_num:03d}"
            title_tpl, d_type, sys_id = self.rng.choice(doc_templates)
            author = self.rng.choice(self.people).id
            dt = self._rand_dt(start_days_ago=320, end_days_ago=5)
            is_outdated = self.rng.random() < 0.12

            doc = Document(
                id=did,
                title=f"{title_tpl} ({did})",
                doc_type=d_type.value,
                author_id=author,
                system_id=sys_id,
                last_updated=self._format_dt(dt),
                status=DocStatus.OUTDATED.value if is_outdated else DocStatus.ACTIVE.value,
                content=f"Technical documentation {did}: Detailed operational guidelines, architecture decisions, and procedures for {sys_id}.",
            )
            self.documents.append(doc)

        # Create Edges for all Documents
        for doc in self.documents:
            # AUTHORED (Person -> Document)
            self._add_edge(
                source_id=doc.author_id,
                source_label=NodeType.PERSON,
                target_id=doc.id,
                target_label=NodeType.DOCUMENT,
                relation_type=RelationType.AUTHORED,
                properties={"last_updated": doc.last_updated},
            )
            # AFFECTS (Document -> System)
            if doc.system_id:
                self._add_edge(
                    source_id=doc.id,
                    source_label=NodeType.DOCUMENT,
                    target_id=doc.system_id,
                    target_label=NodeType.SYSTEM,
                    relation_type=RelationType.AFFECTS,
                    properties={"doc_type": doc.doc_type},
                )

        # Explicit Scenario Edges:
        # DOC-082 CONTRADICTS ADR-051
        self._add_edge(
            source_id="DOC-082",
            source_label=NodeType.DOCUMENT,
            target_id="ADR-051",
            target_label=NodeType.DECISION,
            relation_type=RelationType.CONTRADICTS,
            properties={"reason": "DOC-082 still instructs engineers to use Kafka for synchronous RPC"},
        )

        # DOC-012 GUIDES_RESOLUTION_OF INC-045 and INC-249
        self._add_edge(
            source_id="DOC-012",
            source_label=NodeType.DOCUMENT,
            target_id="INC-045",
            target_label=NodeType.TICKET,
            relation_type=RelationType.GUIDES_RESOLUTION_OF,
            properties={"runbook_step": "kubectl rollout restart & CUDA cache clear"},
        )
        self._add_edge(
            source_id="DOC-012",
            source_label=NodeType.DOCUMENT,
            target_id="INC-249",
            target_label=NodeType.TICKET,
            relation_type=RelationType.GUIDES_RESOLUTION_OF,
            properties={"runbook_step": "Identical CUDA memory leak symptoms"},
        )

    # -------------------------------------------------------------------------
    # 8. Architectural Decisions (60 Decisions in 20 Evolution Chains)
    # -------------------------------------------------------------------------
    def _generate_decisions(self) -> None:
        """Generate 60 ADRs structured into 20 temporal evolution chains."""

        # 20 Realistic Architectural Evolution Chains
        # Format: (Chain Name, System, [(ADR_ID, Title, Days_Ago, Rationale), ...])
        chains = [
            (
                "Client Communication",
                "frontend-bff-gateway",
                [
                    ("ADR-001", "Short-Polling for Client Status Updates", 360, "Simplicity in early product iterations."),
                    ("ADR-021", "WebSocket Connections for Live Dashboards", 180, "Reduced server polling overhead."),
                    ("ADR-041", "gRPC-Web with Server-Sent Events (SSE) for Real-Time Streaming", 40, "Efficient binary framing and HTTP/2 multiplexing."),
                ],
            ),
            (
                "Service Authentication",
                "auth-service",
                [
                    ("ADR-002", "Static Pre-shared API Keys for Service Communication", 350, "Initial bootstrap service mesh."),
                    ("ADR-022", "RS256 Signed Asymmetric JWT Tokens with JWKS", 170, "Eliminated shared secret management."),
                    ("ADR-042", "Mutual TLS (mTLS) with SPIFFE/SPIRE Ephemeral X.509 Certificates", 35, "Zero-trust cryptographically verifiable workloads."),
                ],
            ),
            (
                "Database Sharding",
                "billing-ledger",
                [
                    ("ADR-003", "Single Monolithic PostgreSQL Instance with Read Replicas", 345, "Rapid ACID transaction guarantees."),
                    ("ADR-023", "Citus Distributed PostgreSQL Sharding by OrgID", 160, "Overcame single-node IOPS saturation."),
                    ("ADR-043", "Distributed Multi-Region Ledger with Raft Consensus", 30, "Strict global serializability and high availability."),
                ],
            ),
            (
                "Cache Invalidation Strategy",
                "redis-state-cluster",
                [
                    ("ADR-004", "Simple Time-to-Live (TTL) Cache Expiration", 340, "Standard 5-minute cache expiration."),
                    ("ADR-024", "Redis Pub/Sub Event-Driven Cache Busting", 155, "Sub-second eviction upon write."),
                    ("ADR-044", "Change-Data-Capture (CDC) via Debezium and Kafka Cache Invalidator", 28, "Guaranteed transaction-ordered cache invalidation."),
                ],
            ),
            (
                "Distributed Tracing",
                "network-mesh-ingress",
                [
                    ("ADR-005", "Structured JSON Logging with Request Correlation IDs", 335, "Minimal logging overhead."),
                    ("ADR-025", "OpenTracing with Zipkin Collector Agent", 150, "End-to-end distributed span tracking."),
                    ("ADR-045", "OpenTelemetry (OTel) Collector with eBPF Automatic Instrumentation", 25, "Low-overhead kernel-level trace capture."),
                ],
            ),
            (
                "Container Orchestration",
                "cloud-cost-optimizer",
                [
                    ("ADR-006", "Docker Compose and Nomad Clusters", 330, "Simpler operational footprint."),
                    ("ADR-026", "Self-Managed Kubernetes on EC2 with Kubeadm", 145, "Standardized container orchestration API."),
                    ("ADR-046", "Managed AWS EKS with Karpenter Autoscaling Just-in-Time", 22, "Fast node provisioning and spot optimization."),
                ],
            ),
            (
                "Secrets Management",
                "secrets-kms-proxy",
                [
                    ("ADR-007", "Environment Variables Injected from Encrypted S3 Bucket", 325, "Basic CI/CD deployment secrecy."),
                    ("ADR-027", "HashiCorp Vault Sidecar Agent with Token Renewal", 140, "Dynamic short-lived credentials."),
                    ("ADR-047", "AWS KMS with External Secrets Operator and IRSA Roles", 20, "Cloud-native Kubernetes RBAC secret binding."),
                ],
            ),
            (
                "Frontend State Management",
                "web-client-spa",
                [
                    ("ADR-008", "Redux Monolithic Store with Redux-Saga", 320, "Centralized global state."),
                    ("ADR-028", "Zustand Lightweight State Slices", 135, "Reduced boilerplate and faster UI rendering."),
                    ("ADR-048", "TanStack Query (React Query) for Server State Caching", 18, "Automatic background revalidation and cache deduplication."),
                ],
            ),
            (
                "Background Job Queue",
                "stripe-webhook-worker",
                [
                    ("ADR-009", "Celery with Redis Broker for Background Tasks", 315, "Standard Python worker architecture."),
                    ("ADR-029", "BullMQ on Redis for Distributed Node.js Queueing", 130, "Job priority and concurrency controls."),
                    ("ADR-049", "Temporal.io Stateful Workflows for Long-Running Sagas", 15, "Resilient distributed transaction coordination."),
                ],
            ),
            (
                "Event Streaming",
                "data-lakehouse-ingest",
                [
                    ("ADR-010", "RabbitMQ Topic Exchanges for Event Distribution", 310, "Flexible AMQP routing keys."),
                    ("ADR-030", "Apache Kafka Multi-Node Cluster on NVMe EBS", 125, "High-throughput persistent log retention."),
                    ("ADR-050", "Apache Kafka with Tiered Storage to S3 and Compacted Topics", 12, "Infinite retention and decoupled compute/storage cost."),
                ],
            ),
            # CHAIN 11 - Golden Scenario 2: Synchronous RPC Architecture Evolution
            (
                "Inter-Service RPC Protocol",
                "kafka-event-bus",
                [
                    ("ADR-018", "Asynchronous & Synchronous RPC via Kafka Topics", 300, "Uniform message bus for all inter-service communications."),
                    ("ADR-051", "Deprecate Synchronous Kafka RPC in Favor of gRPC with Protobuf", 21, "Direct HTTP/2 multiplexing, sub-millisecond latencies, and total immunity to consumer lag deadlocks."),
                    ("ADR-060", "gRPC with eBPF Acceleration and Envoy Mesh Sidecar Proxy", 5, "Kernel bypass socket routing for sub-500 microsecond RPC hops."),
                ],
            ),
            (
                "ML Model Serving",
                "ml-inference-worker",
                [
                    ("ADR-011", "Flask REST API wrapping PyTorch Model", 305, "Rapid model prototyping."),
                    ("ADR-031", "TorchServe with Multi-Worker GPU Allocation", 120, "Batch inference and dynamic worker management."),
                    ("ADR-052", "Triton Inference Server with vLLM PagedAttention Integration", 10, "Continuous batching and optimal GPU memory utilization."),
                ],
            ),
            (
                "CI/CD Pipeline",
                "user-profile-service",
                [
                    ("ADR-012", "Jenkins On-Premise Master-Worker Pipeline", 295, "Custom internal build scripts."),
                    ("ADR-032", "GitHub Actions Enterprise with Self-Hosted Runners", 115, "Tight PR integration and declarative YAML."),
                    ("ADR-053", "ArgoCD GitOps Continuous Delivery with Automated Canary Rollouts", 8, "Declarative Kubernetes state with Prometheus canary gating."),
                ],
            ),
            (
                "Feature Flagging",
                "recommendation-service",
                [
                    ("ADR-013", "In-Memory Configuration Reload via SIGHUP", 290, "Zero external dependencies."),
                    ("ADR-033", "LaunchDarkly Managed SaaS Feature Flags", 110, "Targeted user segmentation and gradual percentage rollouts."),
                    ("ADR-054", "Unleash Self-Hosted with Local Proxy Edge Evaluation", 7, "Zero egress cost and sub-millisecond local evaluation."),
                ],
            ),
            (
                "Rate Limiting Architecture",
                "auth-token-validator",
                [
                    ("ADR-014", "Fixed Window Counter in Application Memory", 285, "Initial burst control."),
                    ("ADR-034", "Distributed Sliding Window Log in Redis Cluster", 105, "Accurate rate limiting across horizontally scaled pods."),
                    ("ADR-055", "Envoy Global Rate Limiting Service (RLS) with Token Bucket", 6, "Low-latency network edge enforcement before backend ingress."),
                ],
            ),
            (
                "Search & Vector Indexing",
                "vector-gateway",
                [
                    ("ADR-015", "PostgreSQL Full-Text Search with GIN Indexes", 280, "Integrated relational search."),
                    ("ADR-035", "Elasticsearch Cluster for Text and Log Search", 100, "High-scale inverted index search."),
                    ("ADR-056", "FalkorDB Graph + Hybrid Dense Vector Search", 5, "Multi-hop graph traversal combined with vector similarity."),
                ],
            ),
            (
                "Telemetry Log Aggregation",
                "metrics-aggregation-pipeline",
                [
                    ("ADR-016", "ELK Stack (Elasticsearch, Logstash, Kibana)", 275, "Comprehensive log visualization."),
                    ("ADR-036", "Fluentbit Log Forwarding to ClickHouse Columnar Store", 95, "Drastic compression and 100x faster log analytics."),
                    ("ADR-057", "Vector.dev + ClickHouse + Grafana Loki Unified Telemetry", 4, "Single agent pipelines for logs, metrics, and traces."),
                ],
            ),
            (
                "Payment Orchestration",
                "checkout-orchestrator",
                [
                    ("ADR-017", "Direct Single Stripe API Integration", 270, "Rapid market launch."),
                    ("ADR-037", "Dual Gateway Fallback (Stripe + Adyen)", 90, "Payment processing redundancy."),
                    ("ADR-058", "Smart Routing Engine with Machine Learning Fraud Scoring", 3, "Maximizes authorization rate while minimizing transaction fees."),
                ],
            ),
            (
                "API Gateway Architecture",
                "network-mesh-ingress",
                [
                    ("ADR-019", "Nginx Reverse Proxy with Lua Scripts", 265, "Standard HTTP load balancing."),
                    ("ADR-038", "Kong Gateway Enterprise on Kubernetes", 85, "Plugin ecosystem for authentication and rate limiting."),
                    ("ADR-059", "Envoy Gateway API with eBPF Accelerated Routing", 2, "Modern Kubernetes Gateway API standard with ultra-low latency."),
                ],
            ),
            (
                "Lakehouse Storage Format",
                "data-lakehouse-ingest",
                [
                    ("ADR-020", "Daily S3 CSV and JSON Dumps", 260, "Basic raw data archival."),
                    ("ADR-039", "Apache Parquet on AWS S3 with Glue Metastore", 80, "Columnar compression and fast SQL queries."),
                    ("ADR-040", "Apache Iceberg Open Table Format with Branching & Time-Travel", 1, "ACID transactions, schema evolution, and instantaneous rollback."),
                ],
            ),
        ]

        for chain_idx, (topic, sys_id, steps) in enumerate(chains):
            prev_adr_id: Optional[str] = None

            for step_idx, (adr_id, title, days_ago, rationale) in enumerate(steps):
                is_latest = (step_idx == len(steps) - 1)
                decided_dt = self.base_date - timedelta(days=days_ago)
                author = self.rng.choice(self.people).id

                # For Golden Scenario 2: Liam Chen authored ADR-051
                if adr_id == "ADR-051":
                    author = "person-04"  # Liam Chen
                    source_slack = "SLACK-088"
                    source_ticket = "INC-204"
                else:
                    source_slack = self.rng.choice(self.slack_threads).id if self.rng.random() > 0.5 else None
                    source_ticket = self.rng.choice(self.tickets).id if self.rng.random() > 0.5 else None

                # Invalidation timestamp if superseded
                invalidated_dt = None
                if not is_latest:
                    next_step = steps[step_idx + 1]
                    next_days_ago = next_step[2]
                    invalidated_dt = self._format_dt(self.base_date - timedelta(days=next_days_ago))

                decision = Decision(
                    id=adr_id,
                    title=title,
                    topic=topic,
                    status=DecisionStatus.ACTIVE.value if is_latest else DecisionStatus.SUPERSEDED.value,
                    decided_at=self._format_dt(decided_dt),
                    invalidated_at=invalidated_dt,
                    author_id=author,
                    system_id=sys_id,
                    source_slack_id=source_slack,
                    source_ticket_id=source_ticket,
                    supersedes_decision_id=prev_adr_id,
                    rationale=rationale,
                )
                self.decisions.append(decision)
                self.decisions_by_id[adr_id] = decision

                # Edge: AUTHORED (Person -> Decision)
                self._add_edge(
                    source_id=author,
                    source_label=NodeType.PERSON,
                    target_id=adr_id,
                    target_label=NodeType.DECISION,
                    relation_type=RelationType.AUTHORED,
                    properties={"decided_at": decision.decided_at},
                )

                # Edge: AFFECTS (Decision -> System)
                self._add_edge(
                    source_id=adr_id,
                    source_label=NodeType.DECISION,
                    target_id=sys_id,
                    target_label=NodeType.SYSTEM,
                    relation_type=RelationType.AFFECTS,
                    properties={"status": decision.status},
                )

                # Edge: SUPERSEDES (Decision -> Decision)
                if prev_adr_id:
                    self._add_edge(
                        source_id=adr_id,
                        source_label=NodeType.DECISION,
                        target_id=prev_adr_id,
                        target_label=NodeType.DECISION,
                        relation_type=RelationType.SUPERSEDES,
                        properties={"transition_date": decision.decided_at},
                    )

                # Edge: TRIGGERED_DECISION (Ticket -> Decision)
                if source_ticket:
                    self._add_edge(
                        source_id=source_ticket,
                        source_label=NodeType.TICKET,
                        target_id=adr_id,
                        target_label=NodeType.DECISION,
                        relation_type=RelationType.TRIGGERED_DECISION,
                        properties={"topic": topic},
                    )

                prev_adr_id = adr_id

    # -------------------------------------------------------------------------
    # Public Execution & Export
    # -------------------------------------------------------------------------
    def generate_all(self) -> GraphBundle:
        """Run complete generation pipeline."""
        self._generate_teams()
        self._generate_people()
        self._generate_systems()
        self._generate_tickets()
        self._generate_pull_requests()
        self._generate_slack_threads()
        self._generate_documents()
        self._generate_decisions()

        bundle = GraphBundle(
            teams=self.teams,
            people=self.people,
            systems=self.systems,
            tickets=self.tickets,
            pull_requests=self.pull_requests,
            slack_threads=self.slack_threads,
            documents=self.documents,
            decisions=self.decisions,
            edges=self.edges,
        )
        return bundle

    def export_raw_json(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Export all individual silos and unified graph_bundle.json."""
        target_dir = output_dir or DATA_RAW_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        exported_files: Dict[str, Path] = {}

        def _dump(data: Any, filename: str) -> Path:
            p = target_dir / filename
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            exported_files[filename] = p
            return p

        _dump([t.model_dump(mode="json") for t in self.teams], "teams.json")
        _dump([p.model_dump(mode="json") for p in self.people], "people.json")
        _dump([s.model_dump(mode="json") for s in self.systems], "systems.json")
        _dump([tk.model_dump(mode="json") for tk in self.tickets], "tickets.json")
        _dump([pr.model_dump(mode="json") for pr in self.pull_requests], "pull_requests.json")
        _dump([st.model_dump(mode="json") for st in self.slack_threads], "slack_threads.json")
        _dump([d.model_dump(mode="json") for d in self.documents], "documents.json")
        _dump([dec.model_dump(mode="json") for dec in self.decisions], "decisions.json")
        _dump([e.model_dump(mode="json") for e in self.edges], "edges.json")

        bundle = GraphBundle(
            teams=self.teams,
            people=self.people,
            systems=self.systems,
            tickets=self.tickets,
            pull_requests=self.pull_requests,
            slack_threads=self.slack_threads,
            documents=self.documents,
            decisions=self.decisions,
            edges=self.edges,
        )
        _dump(bundle.model_dump(mode="json"), "graph_bundle.json")

        return exported_files

    def export_processed_csv(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Export nodes and edges as CSV for instant spreadsheet or graph visualizer inspection."""
        target_dir = output_dir or DATA_PROCESSED_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        import csv

        edges_csv = target_dir / "graph_edges.csv"
        with open(edges_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["source_id", "source_label", "target_id", "target_label", "relation_type", "properties"])
            for e in self.edges:
                writer.writerow([
                    e.source_id,
                    e.source_label,
                    e.target_id,
                    e.target_label,
                    e.relation_type,
                    json.dumps(e.properties),
                ])

        nodes_csv = target_dir / "graph_nodes_summary.csv"
        with open(nodes_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "label", "name_or_title", "extra_info"])
            for t in self.teams:
                writer.writerow([t.id, "Team", t.name, t.department])
            for p in self.people:
                writer.writerow([p.id, "Person", p.name, f"{p.role} ({p.team_id})"])
            for s in self.systems:
                writer.writerow([s.id, "System", s.name, f"{s.tier} / {s.language}"])
            for tk in self.tickets:
                writer.writerow([tk.id, "Ticket", tk.title, f"{tk.severity} / {tk.status}"])
            for pr in self.pull_requests:
                writer.writerow([pr.id, "PullRequest", pr.title, f"Author: {pr.author_id}"])
            for st in self.slack_threads:
                writer.writerow([st.id, "SlackThread", st.channel, f"Msgs: {len(st.messages)}"])
            for d in self.documents:
                writer.writerow([d.id, "Document", d.title, f"{d.doc_type} / {d.status}"])
            for dec in self.decisions:
                writer.writerow([dec.id, "Decision", dec.title, f"{dec.status} (Chain: {dec.topic})"])

        return {"edges_csv": edges_csv, "nodes_csv": nodes_csv}

    def verify_golden_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Verify presence and connectivity of the 5 Golden Demo Scenarios."""
        results: Dict[str, Dict[str, Any]] = {}

        # 1. Shadow Ownership
        p19_auth_tickets = [
            t for t in self.tickets
            if t.assignee_id == "person-19" and t.affected_system_id == "auth-service" and t.severity == "SEV-1"
        ]
        p19_auth_prs = [
            pr for pr in self.pull_requests
            if pr.author_id == "person-19" and pr.system_id == "auth-service"
        ]
        results["Scenario 1: Shadow Ownership"] = {
            "verified": len(p19_auth_tickets) >= 18 and len(p19_auth_prs) >= 25,
            "details": f"Elena Rostova (person-19) resolved {len(p19_auth_tickets)} SEV-1s and authored {len(p19_auth_prs)} PRs on auth-service.",
        }

        # 2. Temporal Decision Flip
        doc_contradict = any(
            e.source_id == "DOC-082" and e.target_id == "ADR-051" and e.relation_type == "CONTRADICTS"
            for e in self.edges
        )
        adr_supersedes = any(
            e.source_id == "ADR-051" and e.target_id == "ADR-018" and e.relation_type == "SUPERSEDES"
            for e in self.edges
        )
        results["Scenario 2: Temporal Decision Flip"] = {
            "verified": doc_contradict and adr_supersedes and "SLACK-088" in [st.id for st in self.slack_threads],
            "details": f"ADR-051 supersedes ADR-018, contradicted by outdated DOC-082, discussed in SLACK-088.",
        }

        # 3. 4-Hop Cascading Blast Radius
        # stripe-webhook-worker -> checkout-orchestrator -> auth-token-validator -> redis-session-store
        deps = {(e.source_id, e.target_id) for e in self.edges if e.relation_type == "DEPENDS_ON"}
        has_chain = (
            ("stripe-webhook-worker", "checkout-orchestrator") in deps
            and ("checkout-orchestrator", "auth-token-validator") in deps
            and ("auth-token-validator", "redis-session-store") in deps
        )
        results["Scenario 3: 4-Hop Blast Radius"] = {
            "verified": has_chain and "INC-119" in self.tickets_by_id,
            "details": "Verified 4-hop chain spanning 3 teams with catalyst incident INC-119.",
        }

        # 4. Cross-Agent Incident Memory
        inc_045_runbook = any(
            e.source_id == "DOC-012" and e.target_id == "INC-045" and e.relation_type == "GUIDES_RESOLUTION_OF"
            for e in self.edges
        )
        inc_249_runbook = any(
            e.source_id == "DOC-012" and e.target_id == "INC-249" and e.relation_type == "GUIDES_RESOLUTION_OF"
            for e in self.edges
        )
        results["Scenario 4: Cross-Agent Incident Memory"] = {
            "verified": inc_045_runbook and inc_249_runbook,
            "details": "DOC-012 runbook linked via GUIDES_RESOLUTION_OF to both INC-045 and resurfaced INC-249.",
        }

        # 5. Undocumented Breaking Change
        pr_398_exists = "PR-398" in [pr.id for pr in self.pull_requests]
        inc_250_exists = "INC-250" in self.tickets_by_id
        results["Scenario 5: Undocumented API Breaking Change"] = {
            "verified": pr_398_exists and inc_250_exists,
            "details": "PR-398 modified user-profile-service causing unmarshaling crash INC-250 on recommendation-service.",
        }

        return results

    def print_summary(self) -> None:
        """Print rich console summary of generated knowledge graph."""
        try:
            from tabulate import tabulate
        except ImportError:
            tabulate = None

        node_stats = [
            ("Teams", len(self.teams), "Organizational departments & communication channels"),
            ("People (Staff)", len(self.people), "Engineers, Architects, Leads across 8 teams"),
            ("Systems (Services)", len(self.systems), "Tier-0 to Tier-3 Microservices, Infra & Caches"),
            ("Tickets (Incidents & Tasks)", len(self.tickets), "SEV-1 to SEV-4 Jira/Linear tracking records"),
            ("Pull Requests (GitHub)", len(self.pull_requests), "Code reviews, diffs, and system modifications"),
            ("Slack Threads (Discussions)", len(self.slack_threads), "Multi-turn incident war-rooms & design debates"),
            ("Documents (Runbooks & RFCs)", len(self.documents), "Active and outdated operational guides"),
            ("Decisions (ADRs)", len(self.decisions), "20 Temporal Evolution Chains of architecture choices"),
        ]
        total_nodes = sum(s[1] for s in node_stats)

        # Count relation types
        relation_counts: Dict[str, int] = {}
        for e in self.edges:
            relation_counts[e.relation_type] = relation_counts.get(e.relation_type, 0) + 1

        edge_stats = [(r, cnt) for r, cnt in sorted(relation_counts.items(), key=lambda x: x[1], reverse=True)]
        total_edges = len(self.edges)

        print("\n" + "=" * 80)
        print("[NEXUSBRAIN] 7BIT CLOUD TECHNOLOGIES KNOWLEDGE GRAPH SIMULATION")
        print("=" * 80)

        if tabulate:
            print("\n[+] NODE INVENTORY (Total: {:,})".format(total_nodes))
            print(tabulate(node_stats, headers=["Node Type", "Count", "Description"], tablefmt="grid"))

            print(f"\n[+] EDGE RELATIONSHIPS (Total: {total_edges:,})")
            print(tabulate(edge_stats, headers=["Relation Type", "Count"], tablefmt="grid"))
        else:
            print(f"\nTotal Nodes: {total_nodes}")
            for n, c, d in node_stats:
                print(f"  - {n:30s}: {c:5d} ({d})")
            print(f"\nTotal Edges: {total_edges}")
            for r, c in edge_stats:
                print(f"  - {r:30s}: {c:5d}")

        print("\n" + "-" * 80)
        print("[*] VERIFICATION OF 5 GOLDEN DEMO SCENARIOS")
        print("-" * 80)
        verifications = self.verify_golden_scenarios()
        for scenario_name, data in verifications.items():
            status = "[PASS]" if data["verified"] else "[FAIL]"
            print(f"{status} | {scenario_name}")
            print(f"       -> {data['details']}")
        print("=" * 80 + "\n")


def main() -> None:
    """CLI execution entrypoint."""
    ensure_directories()
    generator = EnterpriseDataGenerator(seed=settings.RANDOM_SEED)
    print("Generating synthetic enterprise dataset for 7bit Cloud Technologies...")
    generator.generate_all()

    print(f"Exporting raw JSON files to: {DATA_RAW_DIR}")
    exported_raw = generator.export_raw_json(DATA_RAW_DIR)
    for name, path in exported_raw.items():
        print(f"  [OK] Written: {path.name} ({path.stat().st_size:,} bytes)")

    print(f"Exporting processed CSV files to: {DATA_PROCESSED_DIR}")
    exported_csv = generator.export_processed_csv(DATA_PROCESSED_DIR)
    for name, path in exported_csv.items():
        print(f"  [OK] Written: {path.name} ({path.stat().st_size:,} bytes)")

    generator.print_summary()


if __name__ == "__main__":
    main()
