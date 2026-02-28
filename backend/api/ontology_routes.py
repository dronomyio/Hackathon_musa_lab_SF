"""Ontology API — seed, query, and explore the macro economic knowledge graph."""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("api.ontology")
router = APIRouter(prefix="/api/ontology", tags=["ontology"])


class CausalChainRequest(BaseModel):
    from_domain: str
    to_domain: str
    max_hops: int = 4


class ThresholdRequest(BaseModel):
    indicators: dict


@router.post("/seed")
async def seed():
    """Seed the Neo4j ontology with the full macro economic knowledge graph."""
    try:
        from core.ontology import seed_ontology
        seed_ontology()
        return {"status": "ok", "message": "Ontology seeded successfully"}
    except Exception as e:
        logger.error(f"Ontology seed failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels/{regime}")
async def get_channels(regime: str):
    """Get active transmission channels for a given regime."""
    try:
        from core.ontology import get_active_transmission_channels
        channels = get_active_transmission_channels(regime)
        return {"regime": regime, "channels": channels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/causal-chain")
async def causal_chain(req: CausalChainRequest):
    """Find causal paths between two domains."""
    try:
        from core.ontology import get_causal_chain
        chains = get_causal_chain(req.from_domain, req.to_domain, req.max_hops)
        return {"from": req.from_domain, "to": req.to_domain, "chains": chains}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts")
async def threshold_alerts(req: ThresholdRequest):
    """Check which thresholds are currently firing."""
    try:
        from core.ontology import get_threshold_alerts
        alerts = get_threshold_alerts(req.indicators)
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def ontology_health():
    """Check Neo4j connectivity."""
    try:
        from core.ontology import get_driver
        driver = get_driver()
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS count")
            count = result.single()["count"]
        driver.close()
        return {"status": "ok", "node_count": count}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}
