"""Multi-Agent Coordinator & Tenant Memory Engine."""

__all__ = [
    "AgentCoordinator",
    "RouterAgent",
    "GraphNavigator",
    "MemoryScribe",
    "AgentQueryResponse",
    "AgentTraceStep",
    "CitationItem",
    "SubgraphPayload",
    "SubgraphNode",
    "SubgraphEdge",
]


def __getattr__(name: str):
    if name == "AgentCoordinator":
        from src.agents.coordinator import AgentCoordinator
        return AgentCoordinator
    elif name in ["RouterAgent", "GraphNavigator", "MemoryScribe"]:
        from src.agents.specialists import GraphNavigator, MemoryScribe, RouterAgent
        if name == "RouterAgent":
            return RouterAgent
        elif name == "GraphNavigator":
            return GraphNavigator
        return MemoryScribe
    elif name in ["AgentQueryResponse", "AgentTraceStep", "CitationItem", "SubgraphPayload", "SubgraphNode", "SubgraphEdge"]:
        import src.agents.models as m
        return getattr(m, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
