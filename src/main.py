"""NexusBrain Application Startup & Service Runner.

Coordinates bootstrap auto-seeding of FalkorDB Cloud / local instance,
followed by launching the FastAPI backend and/or Streamlit UI.
"""

import argparse
import logging
import os
import subprocess
import sys
import time

from src.config import settings
from src.graph.auto_seed import CloudBootstrapSeeder

logger = logging.getLogger("nexus_brain.main")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def run_auto_seed(force: bool = False) -> None:
    """Ensure FalkorDB instance is seeded."""
    logger.info("Initializing FalkorDB bootstrap auto-seeder...")
    try:
        seeder = CloudBootstrapSeeder(force=force)
        res = seeder.run()
        logger.info(f"Bootstrap status: {res.get('status')}")
    except Exception as e:
        logger.error(f"Auto-seed encountered an error: {e}")
        # In container environments, don't crash container immediately if FalkorDB is still starting up
        logger.info("Proceeding to service startup...")


def start_services(mode: str = "all") -> None:
    """Launch services based on mode: 'api', 'ui', or 'all'."""
    procs = []

    try:
        if mode in ("api", "all"):
            api_cmd = [
                sys.executable,
                "-m",
                "uvicorn",
                "src.api.server:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ]
            # If server.py exists or placeholder, start it
            logger.info("Starting FastAPI server on http://0.0.0.0:8000 ...")
            p_api = subprocess.Popen(api_cmd)
            procs.append(p_api)

        if mode in ("ui", "all"):
            ui_cmd = [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "src/ui/app.py",
                "--server.port",
                "8501",
                "--server.address",
                "0.0.0.0",
                "--server.headless",
                "true",
            ]
            logger.info("Starting Streamlit UI on http://0.0.0.0:8501 ...")
            p_ui = subprocess.Popen(ui_cmd)
            procs.append(p_ui)

        # Monitor processes
        while True:
            for p in procs:
                ret = p.poll()
                if ret is not None:
                    logger.warning(f"Process {p.args} exited with code {ret}")
            time.sleep(2)

    except KeyboardInterrupt:
        logger.info("Stopping NexusBrain services...")
        for p in procs:
            p.terminate()


def main():
    parser = argparse.ArgumentParser(description="NexusBrain Main Runner")
    parser.add_argument("--mode", choices=["all", "api", "ui", "seed-only"], default="all", help="Service launch mode")
    parser.add_argument("--force-seed", action="store_true", help="Force wipe and re-seed database")
    args = parser.parse_args()

    run_auto_seed(force=args.force_seed)

    if args.mode != "seed-only":
        start_services(mode=args.mode)


if __name__ == "__main__":
    main()
