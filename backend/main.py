"""Treasury Bond Intelligence Agent — FastAPI Application.

Lifecycle:
  1. Startup: AgentLoop begins, runs first cycle immediately
  2. Running: Loop fetches FRED data + runs agents every N seconds
  3. HTTP clients get cached results instantly from /api/agents/latest
  4. WebSocket clients at /ws/agents get pushed every new result
  5. Shutdown: Loop stops gracefully
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.fred_client import FREDClient
from core.agent_loop import AgentLoop
from agents.orchestrator import OrchestratorAgent
from api.routes import router, set_shared_instances
from api.prompt_routes import router as prompt_router
from api.vertical_routes import router as vertical_router, set_fred_client

from api.ontology_routes import router as ontology_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

settings = get_settings()

# Shared instances
fred_client = FREDClient()
orchestrator = OrchestratorAgent(correlation_window=settings.correlation_window)
agent_loop = AgentLoop(
    fred_client=fred_client,
    orchestrator=orchestrator,
    interval_seconds=settings.agent_loop_interval,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage AgentLoop lifecycle."""
    logging.getLogger("agent_loop").info(
        f"Starting AgentLoop (interval={settings.agent_loop_interval}s, "
        f"engine={'opus-4.6' if settings.has_anthropic else 'rule-based'})"
    )
    agent_loop.start()
    yield
    await agent_loop.stop()
    logging.getLogger("agent_loop").info("AgentLoop shut down")


app = FastAPI(
    title="Macro Intelligence Platform",
    description="8 verticals · 120+ FRED series · AI synthesis · Human-curated prompts",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Share instances with routes
set_shared_instances(fred_client, orchestrator, agent_loop)
set_fred_client(fred_client)
app.include_router(router, prefix="/api")
app.include_router(prompt_router)  # /api/prompts/* (prefix in router)
app.include_router(vertical_router)  # /api/verticals, /api/v/{id}/*
app.include_router(router, prefix="/api")
app.include_router(ontology_router)  # /api/ontology/* (seed, channels, causal-chain, alerts)
app.include_router(prompt_router)
app.include_router(vertical_router)
app.include_router(ontology_router)


@app.get("/")
async def root():
    return {
        "service": "Treasury Bond Intelligence Agent",
        "version": "2.0.0",
        "synthesis_engine": "opus-4.6" if settings.has_anthropic else "rule-based",
        "agent_loop": agent_loop.status,
        "endpoints": {
            "latest_result": "/api/agents/latest",
            "force_run": "/api/agents/run-now",
            "loop_status": "/api/agents/status",
            "core_data": "/api/data/core",
            "extended_data": "/api/data/extended",
            "yield_curve": "/api/data/curve",
            "run_agents": "/api/agents/analyze",
            "single_agent": "/api/agents/{agent_name}",
            "websocket": "/ws/agents",
            "health": "/api/health",
        },
    }


# ─── WebSocket: live agent updates ──────────────────────────────────

@app.websocket("/ws/agents")
async def ws_agent_feed(ws: WebSocket):
    """WebSocket endpoint that pushes agent results as they complete.

    Connect from the dashboard:
      const ws = new WebSocket('ws://localhost:8000/ws/agents')
      ws.onmessage = (e) => setAgentResults(JSON.parse(e.data))
    """
    await ws.accept()
    queue = agent_loop.subscribe()

    # Send current cached result immediately if available
    if agent_loop.latest:
        try:
            await ws.send_text(json.dumps(agent_loop.latest, default=str))
        except Exception:
            pass

    try:
        while True:
            # Wait for next agent loop result
            result = await queue.get()
            try:
                await ws.send_text(json.dumps(result, default=str))
            except Exception:
                break
    except WebSocketDisconnect:
        pass
    finally:
        agent_loop.unsubscribe(queue)
