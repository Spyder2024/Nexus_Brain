"""FalkorDB Graph Loader & Deterministic Cypher Engine."""

__all__ = ["FalkorDBLoader", "GraphTools"]


def __getattr__(name: str):
    if name == "FalkorDBLoader":
        from src.graph.loader import FalkorDBLoader
        return FalkorDBLoader
    elif name == "GraphTools":
        from src.graph.tools import GraphTools
        return GraphTools
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
