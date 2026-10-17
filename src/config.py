"""NexusBrain Configuration Module.

Fully typed configuration leveraging Pydantic and pathlib.Path for OS-agnostic path management.
Provides dual-mode FalkorDB connection handling (Local Docker vs. FalkorDB Cloud).
"""

from pathlib import Path
from typing import Any, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project Directory Anchors (OS-agnostic via pathlib)
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"


class NexusBrainSettings(BaseSettings):
    """Application settings with environment variable overrides."""

    # FalkorDB Connection Settings (Dual-mode: Local Docker vs Cloud)
    FALKORDB_HOST: str = "localhost"
    FALKORDB_PORT: int = 6379
    FALKORDB_USERNAME: Optional[str] = None
    FALKORDB_PASSWORD: Optional[str] = None
    FALKORDB_SSL: bool = False
    COMPANY_GRAPH_NAME: str = "company_brain"
    TENANT_GRAPH_PREFIX: str = "memory_tenant_"

    # Runtime Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    RANDOM_SEED: int = 42

    # Path Settings
    PROJECT_ROOT_PATH: Path = PROJECT_ROOT
    DATA_RAW_PATH: Path = DATA_RAW_DIR
    DATA_PROCESSED_PATH: Path = DATA_PROCESSED_DIR

    @field_validator("FALKORDB_HOST", mode="before")
    @classmethod
    def normalize_host(cls, v: Any) -> str:
        """Fallback to localhost if placeholder or empty string is provided."""
        if not v or not isinstance(v, str) or "your-instance-host" in v.strip() or v.strip() == "":
            return "localhost"
        return v.strip()

    @field_validator("FALKORDB_USERNAME", "FALKORDB_PASSWORD", mode="before")
    @classmethod
    def normalize_empty_strings(cls, v: Any) -> Optional[str]:
        """Convert empty strings to None so unauthenticated connections work cleanly."""
        if isinstance(v, str):
            v_stripped = v.strip()
            return v_stripped if v_stripped else None
        return v

    @field_validator("FALKORDB_SSL", mode="before")
    @classmethod
    def parse_ssl_bool(cls, v: Any) -> bool:
        """Parse string or boolean for SSL."""
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "yes", "t")
        return bool(v)

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = NexusBrainSettings()


def ensure_directories() -> None:
    """Ensure all required project runtime directories exist safely without deletion."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)


def get_falkordb_client():
    """Return an authenticated FalkorDB client instance matching configuration.

    If configured for localhost and unauthenticated Docker is detected, seamlessly
    connects without failing on residual password placeholders.
    """
    from falkordb import FalkorDB

    try:
        return FalkorDB(
            host=settings.FALKORDB_HOST,
            port=settings.FALKORDB_PORT,
            username=settings.FALKORDB_USERNAME,
            password=settings.FALKORDB_PASSWORD,
            ssl=settings.FALKORDB_SSL,
        )
    except Exception as e:
        err_type = type(e).__name__
        err_msg = str(e).lower()
        is_auth_issue = "authentication" in err_type.lower() or "auth" in err_msg or "password" in err_msg or "username" in err_msg
        # If localhost fails with auth error (e.g. local Docker has no auth enabled)
        if settings.FALKORDB_HOST in ("localhost", "127.0.0.1") and is_auth_issue:
            return FalkorDB(
                host=settings.FALKORDB_HOST,
                port=settings.FALKORDB_PORT,
                username=None,
                password=None,
                ssl=False,
            )
        raise e


def get_company_graph():
    """Return the primary FalkorDB company_brain graph."""
    client = get_falkordb_client()
    return client.select_graph(settings.COMPANY_GRAPH_NAME)


def get_tenant_graph(user_id: str):
    """Return the isolated FalkorDB episodic/procedural memory graph for a user."""
    client = get_falkordb_client()
    tenant_name = f"{settings.TENANT_GRAPH_PREFIX}{user_id}"
    return client.select_graph(tenant_name)


if __name__ == "__main__":
    ensure_directories()
    print("NexusBrain Configuration Initialized.")
    print(f"Root: {PROJECT_ROOT}")
    print(f"Data Raw: {DATA_RAW_DIR}")
    print(
        f"FalkorDB: {settings.FALKORDB_HOST}:{settings.FALKORDB_PORT} "
        f"(Company Graph: {settings.COMPANY_GRAPH_NAME})"
    )
