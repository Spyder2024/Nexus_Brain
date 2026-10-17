"""High-Speed Batch Graph Loader for FalkorDB.

Ingests the synthetic enterprise dataset for "7bit Cloud Technologies" into the
primary 'company_brain' graph using parameterized UNWIND queries for sub-second performance.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import (
    DATA_RAW_DIR,
    get_falkordb_client,
    settings,
)

logger = logging.getLogger("nexus_brain.graph.loader")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class FalkorDBLoader:
    """High-speed batch loader for FalkorDB enterprise graph."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        graph_name: Optional[str] = None,
    ):
        self.host = host or settings.FALKORDB_HOST
        self.port = port or settings.FALKORDB_PORT
        self.username = username or settings.FALKORDB_USERNAME
        self.password = password or settings.FALKORDB_PASSWORD
        self.graph_name = graph_name or settings.COMPANY_GRAPH_NAME

        from falkordb import FalkorDB

        self.client = FalkorDB(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
        )
        self.graph = self.client.select_graph(self.graph_name)

    def ping(self) -> bool:
        """Verify connection to FalkorDB."""
        try:
            res = self.graph.query("RETURN 1 AS ping")
            return len(res.result_set) > 0
        except Exception as e:
            logger.error(f"FalkorDB connection failed: {e}")
            return False

    def create_indexes(self) -> None:
        """Create property indexes for fast multi-hop lookups on key node labels."""
        index_specs = [
            ("Team", "id"),
            ("Team", "name"),
            ("Person", "id"),
            ("Person", "name"),
            ("System", "id"),
            ("System", "name"),
            ("System", "tier"),
            ("Ticket", "id"),
            ("Ticket", "severity"),
            ("Ticket", "status"),
            ("PullRequest", "id"),
            ("SlackThread", "id"),
            ("Document", "id"),
            ("Document", "status"),
            ("Decision", "id"),
            ("Decision", "status"),
            ("Decision", "topic"),
        ]

        logger.info("Creating property indexes on FalkorDB...")
        for label, prop in index_specs:
            # FalkorDB index syntax: CREATE INDEX ON :Label(prop) or CREATE INDEX FOR (n:Label) ON (n.prop)
            queries = [
                f"CREATE INDEX ON :{label}({prop})",
                f"CREATE INDEX FOR (n:{label}) ON (n.{prop})",
            ]
            for q in queries:
                try:
                    self.graph.query(q)
                    break
                except Exception as e:
                    # Ignore if index already exists
                    err_msg = str(e).lower()
                    if "already indexed" in err_msg or "already exists" in err_msg:
                        break
                    continue

    def _sanitize_node_properties(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dict values so FalkorDB primitive/list types are respected and nulls stripped."""
        clean: Dict[str, Any] = {}
        for k, v in item.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif isinstance(v, list):
                # If list of primitives
                if all(isinstance(x, (str, int, float, bool)) for x in v):
                    clean[k] = v
                else:
                    clean[k] = json.dumps(v)
            elif isinstance(v, dict):
                clean[k] = json.dumps(v)
            else:
                clean[k] = str(v)
        return clean

    def load_nodes_batch(self, label: str, items: List[Dict[str, Any]], batch_size: int = 250) -> int:
        """Load nodes with UNWIND in batches."""
        total = len(items)
        sanitized = [self._sanitize_node_properties(x) for x in items]

        query = f"""
        UNWIND $batch AS row
        MERGE (n:{label} {{id: row.id}})
        SET n += row
        """

        for i in range(0, total, batch_size):
            chunk = sanitized[i : i + batch_size]
            self.graph.query(query, {"batch": chunk})

        return total

    def load_edges_batch(self, edges: List[Dict[str, Any]], batch_size: int = 250) -> int:
        """Group edges by (source_label, target_label, relation_type) and batch insert with UNWIND."""
        grouped: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}

        for edge in edges:
            s_lbl = edge["source_label"]
            t_lbl = edge["target_label"]
            rel = edge["relation_type"]
            key = (s_lbl, t_lbl, rel)

            props = edge.get("properties", {})
            clean_props = {k: v for k, v in props.items() if v is not None}

            grouped.setdefault(key, []).append({
                "source_id": edge["source_id"],
                "target_id": edge["target_id"],
                "properties": clean_props,
            })

        total_loaded = 0
        for (s_lbl, t_lbl, rel), edge_list in grouped.items():
            query = f"""
            UNWIND $batch AS row
            MATCH (s:{s_lbl} {{id: row.source_id}})
            MATCH (t:{t_lbl} {{id: row.target_id}})
            MERGE (s)-[r:{rel}]->(t)
            SET r += row.properties
            """
            for i in range(0, len(edge_list), batch_size):
                chunk = edge_list[i : i + batch_size]
                self.graph.query(query, {"batch": chunk})
                total_loaded += len(chunk)

        return total_loaded

    def load_all_from_raw(self, raw_dir: Optional[Path] = None, clear_existing: bool = True) -> Dict[str, int]:
        """Read all JSON silos from data/raw/ and ingest into company_brain."""
        target_dir = raw_dir or DATA_RAW_DIR
        start_time = time.perf_counter()

        if clear_existing:
            logger.info(f"Clearing existing graph data in '{self.graph_name}'...")
            try:
                self.graph.delete()
                # Re-select after delete
                self.graph = self.client.select_graph(self.graph_name)
            except Exception as e:
                logger.warning(f"Graph deletion notice: {e}")

        # Recreate schema indexes
        self.create_indexes()

        # 1. Ingest Nodes
        file_to_label = [
            ("teams.json", "Team"),
            ("people.json", "Person"),
            ("systems.json", "System"),
            ("tickets.json", "Ticket"),
            ("pull_requests.json", "PullRequest"),
            ("slack_threads.json", "SlackThread"),
            ("documents.json", "Document"),
            ("decisions.json", "Decision"),
        ]

        stats: Dict[str, int] = {}
        total_nodes = 0

        for filename, label in file_to_label:
            fpath = target_dir / filename
            if not fpath.exists():
                raise FileNotFoundError(f"Missing required file: {fpath}")
            with open(fpath, "r", encoding="utf-8") as f:
                items = json.load(f)
            count = self.load_nodes_batch(label, items)
            stats[f"nodes_{label.lower()}"] = count
            total_nodes += count
            logger.info(f"  [+] Loaded {count:4d} (:{label}) nodes")

        stats["total_nodes"] = total_nodes

        # 2. Ingest Edges
        edges_file = target_dir / "edges.json"
        if not edges_file.exists():
            raise FileNotFoundError(f"Missing edges file: {edges_file}")

        with open(edges_file, "r", encoding="utf-8") as f:
            edges = json.load(f)

        logger.info(f"Ingesting {len(edges):,} directed edges with UNWIND...")
        total_edges = self.load_edges_batch(edges)
        stats["total_edges"] = total_edges

        elapsed = time.perf_counter() - start_time
        stats["elapsed_seconds"] = round(elapsed, 3)
        logger.info(
            f"FalkorDB Ingestion Complete: {total_nodes:,} nodes & {total_edges:,} edges "
            f"loaded in {elapsed:.3f} seconds!"
        )

        return stats

    def get_graph_stats(self) -> Dict[str, Any]:
        """Query and return node & edge statistics directly from FalkorDB."""
        # Total node count
        res_nodes = self.graph.query("MATCH (n) RETURN count(n) AS cnt")
        total_nodes = res_nodes.result_set[0][0] if res_nodes.result_set else 0

        # Total edge count
        res_edges = self.graph.query("MATCH ()-[r]->() RETURN count(r) AS cnt")
        total_edges = res_edges.result_set[0][0] if res_edges.result_set else 0

        # Node labels breakdown
        res_labels = self.graph.query("MATCH (n) RETURN labels(n)[0] AS lbl, count(n) AS cnt ORDER BY cnt DESC")
        label_counts = {row[0]: row[1] for row in res_labels.result_set}

        # Edge relations breakdown
        res_rels = self.graph.query("MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS cnt ORDER BY cnt DESC")
        rel_counts = {row[0]: row[1] for row in res_rels.result_set}

        return {
            "graph_name": self.graph_name,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "nodes_by_label": label_counts,
            "edges_by_type": rel_counts,
        }


def main():
    """CLI execution entrypoint for FalkorDB batch loader."""
    print("=" * 80)
    print("🚀 NEXUSBRAIN: FALKORDB BATCH INGESTION (PHASE 2)")
    print("=" * 80)

    loader = FalkorDBLoader()
    if not loader.ping():
        print(f"❌ Could not connect to FalkorDB at {loader.host}:{loader.port}.")
        print("Please ensure Docker container is running: 'docker compose up -d'")
        sys.exit(1)

    print(f"✓ Connected to FalkorDB at {loader.host}:{loader.port}")
    stats = loader.load_all_from_raw()

    print("\n--- INGESTION SUMMARY ---")
    for k, v in stats.items():
        print(f"  {k:25s}: {v}")

    db_stats = loader.get_graph_stats()
    print("\n--- LIVE DATABASE VERIFICATION ---")
    print(f"Total Nodes in FalkorDB: {db_stats['total_nodes']:,}")
    print(f"Total Edges in FalkorDB: {db_stats['total_edges']:,}")
    print("=" * 80)


if __name__ == "__main__":
    main()
