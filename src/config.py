"""NexusBrain Configuration Module.

Fully typed configuration leveraging Pydantic and pathlib.Path for OS-agnostic path management.
"""

from pathlib import Path
from typing import Optional
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

    # FalkorDB Graph Settings
    FALKORDB_HOST: str = "localhost"
    FALKORDB_PORT: int = 6379
    FALKORDB_PASSWORD: Optional[str] = None
    FALKORDB_GRAPH_NAME: str = "NexusBrainCompanyGraph"

    # Runtime Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    RANDOM_SEED: int = 42

    # Path Settings
    PROJECT_ROOT_PATH: Path = PROJECT_ROOT
    DATA_RAW_PATH: Path = DATA_RAW_DIR
    DATA_PROCESSED_PATH: Path = DATA_PROCESSED_DIR

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


if __name__ == "__main__":
    ensure_directories()
    print(f"NexusBrain Configuration Initialized.")
    print(f"Root: {PROJECT_ROOT}")
    print(f"Data Raw: {DATA_RAW_DIR}")
    print(f"FalkorDB: {settings.FALKORDB_HOST}:{settings.FALKORDB_PORT} (Graph: {settings.FALKORDB_GRAPH_NAME})")
