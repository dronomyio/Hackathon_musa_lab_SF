"""API routes for the Treasury Bond Agent."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from core.config import get_settings
from core.fred_client import FREDClient
from core.agent_loop import AgentLoop
from data.series_config import (
    CORE_SERIES_IDS, EXTENDED_SERIES_IDS, SERIES_LOOKUP,
    MATURITY_LABELS, MATURITY_SERIES,
)
from agents.orchestrator import OrchestratorAgent

router = APIRouter()

# These get set by main.py via set_shared_instances()
_fred_client: Optional[FREDClient] = None
_orchestrator: Optional[OrchestratorAgent] = None
_agent_loop: Optional[AgentLoop] = None


def set_shared_instances(
    fred: FREDClient, orch: OrchestratorAgent, loop: AgentLoop
):
    """Called by main.py to inject shared singletons."""
    global _fred_client, _orchestrator, _agent_loop
    _fred_client = fred
    _orchestrator = orch
    _agent_loop = loop


# ─── Health ──────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "cache_valid": _fred_client.is_cache_valid if _fred_client else False,
        "last_fetch": _fred_client.fetch_timestamp if _fred_client else None,
        "agent_loop": _agent_loop.status if _agent_loop else None,
    }


# ─── Agent Loop endpoints ───────────────────────────────────────────

@router.get("/agents/latest")
async def get_latest():
    """Get the most recent agent result from the loop cache.
    Returns instantly — no computation, no FRED fetch.
    """
    if not _agent_loop or not _agent_loop.latest:
        raise HTTPException(503, "Agent loop has not completed first run yet. Try again in ~30s.")
    return _agent_loop.latest


@router.get("/agents/status")
async def get_loop_status():
    """Agent loop health and scheduling info."""
    if not _agent_loop:
        raise HTTPException(503, "Agent loop not initialized")
    return _agent_loop.status


@router.post("/agents/run-now")
async def force_run():
    """Trigger an immediate agent loop execution (bypasses interval)."""
    if not _agent_loop:
        raise HTTPException(503, "Agent loop not initialized")
    result = await _agent_loop.run_now()
    return result


# ─── On-demand analysis (bypasses loop, runs fresh) ─────────────────

@router.get("/agents/analyze")
async def run_agents(force: bool = Query(False)):
    """Run all agents on demand (fresh FRED fetch + synthesis).

    Use /agents/latest for cached loop results instead.
    """
    settings = get_settings()
    if not settings.fred_api_key:
        raise HTTPException(500, "FRED_API_KEY not configured")

    data = await _fred_client.fetch_multiple(EXTENDED_SERIES_IDS, force=force)
    result = await _orchestrator.run_all(data)
    return result


@router.get("/agents/{agent_name}")
async def run_single_agent(agent_name: str, force: bool = Query(False)):
    """Run a single named agent."""
    from agents.yield_curve import YieldCurveAgent
    from agents.credit_risk import CreditRiskAgent
    from agents.inflation import InflationAgent
    from agents.tail_risk import TailRiskAgent
    from agents.cross_correlation import CrossCorrelationAgent

    agents = {
        "yield_curve": YieldCurveAgent(),
        "credit_risk": CreditRiskAgent(),
        "inflation": InflationAgent(),
        "tail_risk": TailRiskAgent(),
        "cross_correlation": CrossCorrelationAgent(),
    }

    if agent_name not in agents:
        raise HTTPException(404, f"Unknown agent: {agent_name}. Options: {list(agents.keys())}")

    data = await _fred_client.fetch_multiple(EXTENDED_SERIES_IDS, force=force)
    signal = agents[agent_name].analyze(data)
    return signal.to_dict()


# ─── Data endpoints ─────────────────────────────────────────────────

@router.get("/data/core")
async def get_core_data(force: bool = Query(False)):
    """Fetch core yield curve + spread data."""
    settings = get_settings()
    if not settings.fred_api_key:
        raise HTTPException(500, "FRED_API_KEY not configured")

    data = await _fred_client.fetch_multiple(CORE_SERIES_IDS, force=force)
    return {
        "data": data,
        "fetch_time": _fred_client.fetch_timestamp,
        "errors": _fred_client.errors,
        "series_count": len([k for k, v in data.items() if v]),
    }


@router.get("/data/extended")
async def get_extended_data(force: bool = Query(False)):
    """Fetch all series including credit, inflation, fed policy."""
    settings = get_settings()
    if not settings.fred_api_key:
        raise HTTPException(500, "FRED_API_KEY not configured")

    data = await _fred_client.fetch_multiple(EXTENDED_SERIES_IDS, force=force)
    return {
        "data": data,
        "fetch_time": _fred_client.fetch_timestamp,
        "errors": _fred_client.errors,
        "series_count": len([k for k, v in data.items() if v]),
    }


@router.get("/data/series/{series_id}")
async def get_series(series_id: str, force: bool = Query(False)):
    """Fetch a single series."""
    settings = get_settings()
    if not settings.fred_api_key:
        raise HTTPException(500, "FRED_API_KEY not configured")

    if series_id not in SERIES_LOOKUP:
        raise HTTPException(404, f"Unknown series: {series_id}")

    data = await _fred_client.fetch_multiple([series_id], force=force)
    return {
        "series_id": series_id,
        "name": SERIES_LOOKUP[series_id].name,
        "data": data.get(series_id, []),
        "count": len(data.get(series_id, [])),
    }


@router.get("/data/curve")
async def get_yield_curve(force: bool = Query(False)):
    """Current yield curve snapshot."""
    data = await _fred_client.fetch_multiple(MATURITY_SERIES, force=force)

    current = {}
    prev_30d = {}
    for sid in MATURITY_SERIES:
        obs = data.get(sid, [])
        if obs:
            current[sid] = obs[-1]["value"]
            idx = max(0, len(obs) - 22)
            prev_30d[sid] = obs[idx]["value"]

    return {
        "maturities": MATURITY_LABELS,
        "series_ids": MATURITY_SERIES,
        "current": current,
        "prev_30d": prev_30d,
        "date": data.get("DGS10", [{}])[-1].get("date") if data.get("DGS10") else None,
    }


@router.post("/cache/invalidate")
async def invalidate_cache():
    """Force cache refresh on next request."""
    _fred_client.invalidate_cache()
    return {"status": "cache invalidated"}
