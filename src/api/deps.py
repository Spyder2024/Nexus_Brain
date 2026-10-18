"""NexusBrain API Dependencies & Singleton Backend Lifecycle.

Handles:
- Environment mode selection ('live' vs 'mock')
- Singleton backend initialization
- Background thread auto-seeding with concurrency lock
"""

import logging
import os
import threading
from typing import Optional

from src.api.backend import BackendInterface, LiveBackend
from src.api.mock_bridge import mock_backend

logger = logging.getLogger("nexus_brain.api.deps")

# Global lifecycle flags
_backend_instance: Optional[BackendInterface] = None
_backend_lock = threading.Lock()
_seeding_in_progress = False
_is_seeded = True
_mode_cached = "mock"


def initialize_backend() -> BackendInterface:
    """Initialize singleton backend depending on NEXUS_MODE and connectivity."""
    global _backend_instance, _mode_cached, _seeding_in_progress, _is_seeded

    env_mode = os.environ.get("NEXUS_MODE", "live").lower()

    if env_mode == "mock":
        logger.info("NEXUS_MODE=mock specified. Using MockBackend.")
        _mode_cached = "mock"
        _backend_instance = mock_backend
        _is_seeded = True
        return _backend_instance

    # Attempt LiveBackend
    try:
        live = LiveBackend()
        if live.ping_falkordb():
            logger.info("FalkorDB connection confirmed. Running in LIVE mode.")
            _mode_cached = "live"
            _backend_instance = live

            # Check if seeded or trigger background seed
            stats = live.get_stats()
            if stats.get("nodes", 0) < 100:
                _is_seeded = False
                _trigger_background_seed(live)
            else:
                _is_seeded = True

            return _backend_instance
        else:
            logger.warning("FalkorDB ping failed. Falling back to MockBackend.")
    except Exception as e:
        logger.warning(f"Could not connect to live FalkorDB ({e}). Falling back to MockBackend.")

    _mode_cached = "mock"
    _backend_instance = mock_backend
    _is_seeded = True
    return _backend_instance


def _trigger_background_seed(live_backend: LiveBackend) -> None:
    """Run seeding in a daemon thread so /health answers immediately."""
    global _seeding_in_progress, _is_seeded

    def _worker():
        global _seeding_in_progress, _is_seeded
        with _backend_lock:
            _seeding_in_progress = True
            try:
                logger.info("Starting background auto-seed of company_brain...")
                live_backend.reset_state()
                _is_seeded = True
                logger.info("Background auto-seed completed successfully.")
            except Exception as e:
                logger.error(f"Background auto-seed failed: {e}")
            finally:
                _seeding_in_progress = False

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def get_backend() -> BackendInterface:
    """Return singleton backend."""
    global _backend_instance
    if _backend_instance is None:
        _backend_instance = initialize_backend()
    return _backend_instance


def get_mode() -> str:
    """Return active mode ('live' or 'mock')."""
    return _mode_cached


def is_seeded() -> bool:
    """Return whether initial dataset has been seeded."""
    return _is_seeded


def is_seeding() -> bool:
    """Return whether background seeding is currently underway."""
    return _seeding_in_progress
