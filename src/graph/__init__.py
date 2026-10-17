"""FalkorDB Graph Loader, Deterministic Cypher Engine & Auto-Seeder."""

__all__ = ["FalkorDBLoader", "GraphTools", "CloudBootstrapSeeder"]


def __getattr__(name: str):
    if name == "FalkorDBLoader":
        from src.graph.loader import FalkorDBLoader
        return FalkorDBLoader
    elif name == "GraphTools":
        from src.graph.tools import GraphTools
        return GraphTools
    elif name == "CloudBootstrapSeeder":
        from src.graph.auto_seed import CloudBootstrapSeeder
        return CloudBootstrapSeeder
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
