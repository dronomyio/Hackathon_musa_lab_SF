"""
Vertical API Routes — Multi-vertical macro intelligence platform.

Endpoints:
  GET /api/verticals           → List all verticals (for tab bar)
  GET /api/v/{vid}/config      → Full config for a vertical (charts, kpis, series)
  GET /api/v/{vid}/data        → FRED data for a vertical
  GET /api/v/{vid}/analysis    → AI synthesis for a vertical
"""

import json
import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException

from core.config import get_settings
from core.prompt_lifecycle import get_best_prompt, get_prompt, save_draft, log_run
from data.verticals import (
    VERTICALS, get_vertical, list_verticals as _list_verticals,
    get_all_series_ids, get_prompt_template,
)

log = logging.getLogger("verticals")
router = APIRouter(prefix="/api", tags=["verticals"])

# Caches (refreshed every 15 min by agent loop or on-demand)
_data_cache: dict[str, dict] = {}
_analysis_cache: dict[str, dict] = {}
_fred_client = None


def set_fred_client(client):
    global _fred_client
    _fred_client = client


# ─── List verticals (for tab bar) ─────────────────────────────────

@router.get("/verticals")
async def list_verticals():
    return {"verticals": _list_verticals()}


# ─── Vertical config ──────────────────────────────────────────────

@router.get("/v/{vid}/config")
async def get_config(vid: str):
    v = get_vertical(vid)
    if not v:
        raise HTTPException(404, f"Vertical '{vid}' not found")

    return {
        "id": v["id"],
        "name": v["name"],
        "icon": v["icon"],
        "color": v["color"],
        "is_primary": v.get("is_primary", False),
        "description": v["description"],
        "tagline": v.get("tagline", ""),
        "customers": v.get("customers", []),
        "series_count": len(v.get("series", [])) or 49,
        "kpis": v.get("kpis", []),
        "charts": v.get("charts", []),
    }


# ─── Vertical FRED data ──────────────────────────────────────────

@router.get("/v/{vid}/data")
async def get_data(vid: str):
    v = get_vertical(vid)
    if not v:
        raise HTTPException(404, f"Vertical '{vid}' not found")

    # Primary vertical (DeFi) — data comes from the main agent loop
    if v.get("uses_primary_agents"):
        cached = _data_cache.get(vid, {})
        return {"vertical_id": vid, "data": cached.get("data", {})}

    # Check cache (15 min TTL)
    if vid in _data_cache:
        cached = _data_cache[vid]
        age = (datetime.now() - datetime.fromisoformat(
            cached.get("_at", "2000-01-01")
        )).total_seconds()
        if age < 900:
            return cached

    # Fetch from FRED
    if not _fred_client:
        return {"vertical_id": vid, "data": {}, "error": "FRED client not initialized"}

    series_ids = get_all_series_ids(vid)
    data = {}
    errors = []

    for sid in series_ids:
        try:
            obs = await _fred_client.fetch_series(sid)
            if obs:
                data[sid] = obs
        except Exception as e:
            errors.append(f"{sid}: {e}")

    result = {
        "vertical_id": vid,
        "data": data,
        "series_count": len(data),
        "errors": errors or None,
        "_at": datetime.now().isoformat(),
    }
    _data_cache[vid] = result
    return result


# ─── Vertical AI analysis ────────────────────────────────────────

@router.get("/v/{vid}/analysis")
async def get_analysis(vid: str):
    v = get_vertical(vid)
    if not v:
        raise HTTPException(404, f"Vertical '{vid}' not found")

    # Primary vertical — use main orchestrator results
    if v.get("uses_primary_agents"):
        return _analysis_cache.get(vid, {
            "vertical_id": vid,
            "note": "Use /api/agents/latest for the primary DeFi vertical",
        })

    # Check cache
    if vid in _analysis_cache:
        cached = _analysis_cache[vid]
        age = (datetime.now() - datetime.fromisoformat(
            cached.get("_at", "2000-01-01")
        )).total_seconds()
        if age < 900:
            return cached

    # Need data first
    raw = _data_cache.get(vid)
    if not raw or not raw.get("data"):
        return {"vertical_id": vid, "error": "No data. Fetch /api/v/{vid}/data first."}

    # Build metrics summary from raw data
    metrics = {}
    for sid, obs in raw.get("data", {}).items():
        if isinstance(obs, list) and obs:
            last = obs[-1]
            val = float(last["value"]) if last.get("value") else None
            prev = float(obs[-2]["value"]) if len(obs) > 1 and obs[-2].get("value") else None
            change = ((val - prev) / abs(prev) * 100) if val and prev and prev != 0 else None

            # Look up friendly name from config
            name = sid
            for s in v.get("series", []):
                if s["id"] == sid:
                    name = s["name"]
                    break

            metrics[sid] = {
                "series_name": name,
                "value": val,
                "date": last.get("date"),
                "change_pct": round(change, 2) if change else None,
                "units": next((s.get("units", "") for s in v.get("series", []) if s["id"] == sid), ""),
            }

    settings = get_settings()

    # No API key — return metrics only
    if not settings.has_anthropic:
        result = {
            "vertical_id": vid,
            "metrics": metrics,
            "synthesis": None,
            "prompt_status": "none",
            "_at": datetime.now().isoformat(),
        }
        _analysis_cache[vid] = result
        return result

    # Resolve system prompt via lifecycle
    domains = [vid]
    system_prompt = get_best_prompt(domains)
    prompt_status = "existing"

    if not system_prompt:
        # Bootstrap a new prompt
        system_prompt = await _bootstrap_prompt(v, metrics)
        if system_prompt:
            save_draft(
                domains=domains,
                system_prompt=system_prompt,
                user_intent=v["description"],
                generated_by=f"bootstrap-{vid}",
            )
            prompt_status = "draft"
        else:
            # Use template as fallback
            system_prompt = get_prompt_template(vid) or f"You are a {v['name']} analyst. Analyze the data. Respond in JSON."
            prompt_status = "fallback"
    else:
        entry = get_prompt(domains)
        prompt_status = entry["status"] if entry else "unknown"

    # Run synthesis
    synthesis = await _run_synthesis(v, metrics, system_prompt)

    # Log performance
    if synthesis and isinstance(synthesis, dict):
        log_run(
            domains,
            synthesis.get("confidence", 0.5),
            synthesis.get("market_regime", "unknown"),
            synthesis.get("conflicts", []),
        )

    result = {
        "vertical_id": vid,
        "metrics": metrics,
        "synthesis": synthesis,
        "prompt_status": prompt_status,
        "_at": datetime.now().isoformat(),
    }
    _analysis_cache[vid] = result
    return result


# ─── Bootstrap prompt via Opus 4.6 ───────────────────────────────

async def _bootstrap_prompt(v: dict, metrics: dict) -> str | None:
    settings = get_settings()
    if not settings.has_anthropic:
        return None

    template = get_prompt_template(v["id"])
    series_list = json.dumps(list(metrics.keys()))

    meta = f"""Write a SYSTEM PROMPT for an AI analyst specializing in {v['name']}.

FRED Series available: {series_list}
Focus: {v['description']}
Target customers: {', '.join(v.get('customers', []))}

Base template (expand and improve this):
{template}

Requirements:
1. Define the analyst role clearly
2. Explain what each metric means and its significance
3. Include specific thresholds and triggers
4. Define the JSON response schema:
   market_regime, regime_label, dominant_signal, confidence (0-1),
   headline, narrative (4-5 paragraphs), key_risks (list), regime_triggers (list)
5. Be decisive and quantitative

Write ONLY the system prompt. Start with 'You are...'."""

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.claude_model,
                    "max_tokens": 3000,
                    "messages": [{"role": "user", "content": meta}],
                },
                timeout=90.0,
            )
            resp.raise_for_status()
            text = "".join(
                b["text"] for b in resp.json().get("content", [])
                if b.get("type") == "text"
            ).strip()
            return text
    except Exception as e:
        log.error(f"Bootstrap {v['id']}: {e}")
        return None


# ─── Run synthesis via Opus 4.6 ──────────────────────────────────

async def _run_synthesis(v: dict, metrics: dict, system_prompt: str) -> dict:
    settings = get_settings()

    user_prompt = f"""Current date: {datetime.now().strftime('%Y-%m-%d')}

## {v['name']} — Latest Metrics

{json.dumps(metrics, indent=2, default=str)}

Analyze these metrics. Respond ONLY with valid JSON, no markdown fences."""

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.claude_model,
                    "max_tokens": 2000,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            text = "".join(
                b["text"] for b in resp.json().get("content", [])
                if b.get("type") == "text"
            ).strip()

            # Parse JSON (handle markdown fences)
            if "```" in text:
                for part in text.split("```"):
                    clean = part.strip()
                    if clean.startswith("json"):
                        clean = clean[4:].strip()
                    try:
                        return json.loads(clean)
                    except json.JSONDecodeError:
                        continue
            return json.loads(text)

    except json.JSONDecodeError:
        return {
            "market_regime": "unknown",
            "headline": "Analysis completed (non-JSON response)",
            "narrative": text if "text" in dir() else "",
            "confidence": 0.5,
        }
    except Exception as e:
        return {
            "market_regime": "error",
            "headline": f"Synthesis failed: {str(e)[:100]}",
            "confidence": 0,
        }


# ─── Cache update (called by agent loop for primary vertical) ────

def update_primary_cache(results: dict):
    """Called by AgentLoop to update the DeFi/crypto vertical cache."""
    _data_cache["defi_crypto"] = {
        "vertical_id": "defi_crypto",
        "data": results.get("_raw_data", {}),
    }
    _analysis_cache["defi_crypto"] = {
        "vertical_id": "defi_crypto",
        "synthesis": results.get("synthesis"),
        "metrics": {k: v for k, v in results.get("signals", {}).items()},
        "prompt_status": results.get("prompt_status", "unknown"),
        "_at": datetime.now().isoformat(),
    }
