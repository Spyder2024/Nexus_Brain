"""Idempotent Cloud Auto-Seeder for FalkorDB Cloud & Local Deployments.

Ensures the FalkorDB instance (company_brain graph) is properly seeded with the
enterprise dataset upon container startup or initial setup.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any

from src.config import (
    DATA_RAW_DIR,
    ensure_directories,
    get_falkordb_client,
    settings,
)
from src.data_gen.company_generator import EnterpriseDataGenerator
from src.graph.loader import FalkorDBLoader

logger = logging.getLogger("nexus_brain.graph.auto_seed")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class CloudBootstrapSeeder:
    """Idempotent FalkorDB Cloud & local database bootstrap seeder."""

    def __init__(self, force: bool = False, min_nodes_threshold: int = 100):
        self.force = force
        self.min_nodes_threshold = min_nodes_threshold
        ensure_directories()
        self.loader = FalkorDBLoader()
        self.client = self.loader.client
        self.graph = self.loader.graph

    def check_existing_node_count(self) -> int:
        """Query total node count in the company_brain graph."""
        try:
            res = self.graph.query("MATCH (n) RETURN count(n) AS total")
            if res and res.result_set:
                return int(res.result_set[0][0])
            return 0
        except Exception as e:
            logger.warning(f"Could not check existing node count: {e}. Assuming unseeded (0).")
            return 0

    def ensure_raw_dataset_exists(self) -> None:
        """Verify data/raw/*.json exists; generate deterministically if missing."""
        raw_teams_file = DATA_RAW_DIR / "teams.json"
        if not raw_teams_file.exists():
            logger.info("Raw enterprise dataset not found in data/raw/. Generating synthetic dataset (seed=42)...")
            gen = EnterpriseDataGenerator(seed=settings.RANDOM_SEED)
            gen.generate_all()
            gen.export_raw_json()
            gen.export_processed_csv()
            logger.info("Dataset generation complete.")
        else:
            logger.info(f"Raw enterprise dataset confirmed present in {DATA_RAW_DIR}.")

    def run(self) -> Dict[str, Any]:
        """Execute idempotent bootstrap sequence."""
        t0 = time.perf_counter()
        logger.info(f"Connecting to FalkorDB at {settings.FALKORDB_HOST}:{settings.FALKORDB_PORT} (SSL: {settings.FALKORDB_SSL})...")

        # Check ping
        if not self.loader.ping():
            raise ConnectionError(f"Could not connect to FalkorDB at {settings.FALKORDB_HOST}:{settings.FALKORDB_PORT}")

        total_nodes = self.check_existing_node_count()

        if total_nodes >= self.min_nodes_threshold and not self.force:
            logger.info(
                f"FalkorDB Cloud already seeded with {total_nodes} nodes (threshold: {self.min_nodes_threshold}). "
                "Skipping bootstrap."
            )
            return {
                "status": "skipped",
                "total_nodes": total_nodes,
                "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            }

        if self.force:
            logger.warning("Force flag enabled. Re-seeding FalkorDB graph...")
            try:
                self.graph.delete()
                # Re-select graph after delete
                self.graph = self.client.select_graph(settings.COMPANY_GRAPH_NAME)
                self.loader.graph = self.graph
            except Exception as e:
                logger.warning(f"Could not delete graph for re-seed: {e}")

        # Ensure raw JSON files exist
        self.ensure_raw_dataset_exists()

        # Ingest dataset using fast batch loader
        logger.info("Seeding FalkorDB graph with enterprise dataset...")
        stats = self.loader.load_all_from_raw()

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        logger.info(
            f"FalkorDB graph successfully seeded in {elapsed_ms}ms! "
            f"Total Nodes: {stats.get('total_nodes', 'unknown')}, Total Edges: {stats.get('total_edges', 'unknown')}"
        )

        return {
            "status": "seeded",
            "stats": stats,
            "latency_ms": elapsed_ms,
        }


def main():
    """CLI entrypoint for auto-seeder."""
    parser = argparse.ArgumentParser(description="NexusBrain FalkorDB Auto-Seeder")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force wipe and re-seed FalkorDB company_brain graph",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=100,
        help="Minimum node threshold to consider database already seeded (default: 100)",
    )
    args = parser.parse_args()

    seeder = CloudBootstrapSeeder(force=args.force, min_nodes_threshold=args.threshold)
    result = seeder.run()
    logger.info(f"Auto-seed completed: {result['status']}")


if __name__ == "__main__":
    main()
