"""FastAPI Production Server for NexusBrain.

Implements DEV_B_SPEC_v2.md Section 2 API contract:
- GET  /api/v1/health
- GET  /api/v1/stats?user_id=meera
- POST /api/v1/query
- POST /api/v1/mutate
- GET  /api/v1/memory/{user_id}
- POST /api/v1/reset

Standardized error envelope: {"error": {"code": str, "message": str}}
"""

from datetime import datetime, timezone
import os
import re
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.deps import get_backend, get_mode, is_seeded, is_seeding, initialize_backend
from src.api.mock_bridge import ConflictError
from src.api.schemas import (
    ErrorEnvelope,
    HealthResponse,
    MemoryResponse,
    MutateRequest,
    MutateResponse,
    QueryRequest,
    ResetResponse,
    StatsResponse,
)
from src.schema.models import AgentQueryResponse

app = FastAPI(
    title="NexusBrain API",
    description="Graph-Native Company Brain & Multi-Agent Memory Coordinator",
    version="2.0.0",
)

# Configure CORS
cors_origins_env = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize singleton backend on boot."""
    initialize_backend()


# Standardized error handlers
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    msg = errors[0].get("msg", "Validation error") if errors else "Invalid request payload"
    loc = errors[0].get("loc", []) if errors else []
    field = ".".join(str(l) for l in loc) if loc else "body"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": "VALIDATION_ERROR", "message": f"{field}: {msg}"}},
    )


@app.exception_handler(ConflictError)
def conflict_exception_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": {"code": "CONFLICT", "message": str(exc)}},
    )


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
    )


@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": str(exc)}},
    )


# ----------------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------------

@app.get("/api/v1/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Fast keep-alive check. Answers in < 1 second without blocking."""
    backend = get_backend()
    connected = backend.ping_falkordb()
    mode = get_mode()
    seeded = is_seeded()

    return HealthResponse(
        status="awake",
        falkordb_connected=connected,
        seeded=seeded,
        mode=mode,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/v1/stats", response_model=StatsResponse)
def get_stats(user_id: str = "meera") -> StatsResponse:
    """Return live node/edge counts, graph list, and query latency."""
    backend = get_backend()
    data = backend.get_stats(user_id=user_id)
    return StatsResponse(
        mode=data.get("mode", get_mode()),
        nodes=data.get("nodes", 1077),
        edges=data.get("edges", 4103),
        graphs=data.get("graphs", ["company_brain"]),
        active_tenant_graph=data.get("active_tenant_graph", f"memory_tenant_{user_id}"),
        avg_query_ms=data.get("avg_query_ms", 3.8),
    )


@app.post("/api/v1/query", response_model=AgentQueryResponse)
def post_query(payload: QueryRequest) -> AgentQueryResponse:
    """Ask the Company Brain using multi-agent graph navigation."""
    if is_seeding():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is currently seeding. Please retry in a few seconds.",
        )

    backend = get_backend()
    return backend.handle_query(
        user_id=payload.user_id,
        query=payload.query,
        session_id=payload.session_id,
    )


@app.post("/api/v1/mutate", response_model=MutateResponse)
def post_mutate(payload: MutateRequest) -> MutateResponse:
    """Inject a new decision into the graph, invalidating the previous active standard."""
    backend = get_backend()
    res = backend.mutate_knowledge(
        user_id=payload.user_id,
        source_type=payload.source_type,
        channel=payload.channel,
        system_name=payload.system_name,
        new_decision_title=payload.new_decision_title,
        supersedes_decision_id=payload.supersedes_decision_id,
        rationale=payload.rationale,
    )
    return MutateResponse(
        new_decision=res["new_decision"],
        superseded_decision=res["superseded_decision"],
        subgraph=res["subgraph"],
        latency_ms=res["latency_ms"],
        cypher_executed=res["cypher_executed"],
    )


@app.get("/api/v1/memory/{user_id}", response_model=MemoryResponse)
def get_memory(user_id: str) -> MemoryResponse:
    """Return isolated episodic conversation turns and shared procedural playbooks."""
    backend = get_backend()
    mem = backend.get_memory(user_id=user_id)
    return MemoryResponse(
        tenant_graph=mem["tenant_graph"],
        turns=mem.get("turns", []),
        playbooks=mem.get("playbooks", []),
        shared_playbooks=mem.get("shared_playbooks", []),
    )


@app.post("/api/v1/reset", response_model=ResetResponse)
def post_reset(x_admin_token: Optional[str] = Header(None)) -> ResetResponse:
    """Reset the knowledge graph to pristine baseline Golden Scenarios."""
    admin_token = os.environ.get("ADMIN_TOKEN")
    if admin_token and x_admin_token != admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Valid X-Admin-Token header required.",
        )

    backend = get_backend()
    res = backend.reset_state()
    return ResetResponse(
        reseeded=res.get("reseeded", True),
        nodes=res.get("nodes", 1077),
        edges=res.get("edges", 4103),
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=port, reload=True)
