"""
Prompt Lifecycle API Routes — Human-in-the-loop prompt curation.

Endpoints:
  GET  /api/prompts              → List all prompts with status
  GET  /api/prompts/active       → Get the active prompt for current domains
  POST /api/prompts/curate       → Human approves/edits a prompt → CURATED
  POST /api/prompts/rollback     → Roll back to a previous version
  GET  /api/prompts/improve      → Ask Opus 4.6 for improvement suggestions
  GET  /api/prompts/performance  → Performance metrics for active prompt
  POST /api/prompts/reset        → Delete prompt, force re-bootstrap on next run
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.prompt_lifecycle import (
    list_prompts, get_prompt, curate_prompt, rollback, delete_prompt,
)
from agents.orchestrator import ACTIVE_DOMAINS, OrchestratorAgent


router = APIRouter(prefix="/api/prompts", tags=["prompts"])

# Shared orchestrator instance for self-improvement calls
_orchestrator = OrchestratorAgent()


class CurateRequest(BaseModel):
    edited_prompt: Optional[str] = None
    curator: str = "human"
    notes: str = ""


class RollbackRequest(BaseModel):
    version: int


# ─── List all prompts ─────────────────────────────────────────────

@router.get("/")
async def list_all_prompts(status: Optional[str] = None):
    """List all prompts, optionally filtered by status (draft|evolving|curated)."""
    prompts = list_prompts(status=status)
    return {
        "count": len(prompts),
        "prompts": [
            {
                "key": p["key"],
                "domains": p["domains"],
                "status": p["status"],
                "version": p["version"],
                "created_at": p.get("created_at"),
                "updated_at": p.get("updated_at"),
                "curated_at": p.get("curated_at"),
                "curated_by": p.get("curated_by"),
                "runs": p.get("performance", {}).get("runs", 0),
                "avg_confidence": p.get("performance", {}).get("avg_confidence", 0),
            }
            for p in prompts
        ],
    }


# ─── Get active prompt ────────────────────────────────────────────

@router.get("/active")
async def get_active_prompt():
    """Get the full active prompt entry for current domains."""
    entry = get_prompt(ACTIVE_DOMAINS)
    if not entry:
        return {
            "status": "none",
            "message": "No prompt exists yet. It will be auto-generated on next synthesis run.",
            "domains": ACTIVE_DOMAINS,
        }

    return {
        "key": entry["key"],
        "domains": entry["domains"],
        "status": entry["status"],
        "version": entry["version"],
        "system_prompt": entry["system_prompt"],
        "user_intent": entry.get("user_intent", ""),
        "generated_by": entry.get("generated_by", ""),
        "created_at": entry.get("created_at"),
        "updated_at": entry.get("updated_at"),
        "curated_at": entry.get("curated_at"),
        "curated_by": entry.get("curated_by"),
        "human_notes": entry.get("human_notes", ""),
        "performance": entry.get("performance", {}),
        "history": [
            {"version": h["version"], "status": h["status"], "saved_at": h["saved_at"]}
            for h in entry.get("history", [])
        ],
    }


# ─── Curate (human approves / edits) ─────────────────────────────

@router.post("/curate")
async def curate_active_prompt(req: CurateRequest):
    """
    Human reviews and optionally edits the active prompt.
    Changes status to CURATED — Opus 4.6 will never auto-overwrite a curated prompt.
    """
    try:
        entry = curate_prompt(
            domains=ACTIVE_DOMAINS,
            edited_prompt=req.edited_prompt,
            curator=req.curator,
            notes=req.notes,
        )
        return {
            "status": "curated",
            "version": entry["version"],
            "curated_at": entry["curated_at"],
            "curated_by": entry["curated_by"],
            "message": "Prompt curated successfully. Opus 4.6 will use this version.",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─── Rollback ─────────────────────────────────────────────────────

@router.post("/rollback")
async def rollback_prompt(req: RollbackRequest):
    """Roll back the active prompt to a previous version."""
    try:
        entry = rollback(domains=ACTIVE_DOMAINS, to_version=req.version)
        return {
            "status": entry["status"],
            "version": entry["version"],
            "message": f"Rolled back to version {req.version}.",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─── Self-improvement suggestions ─────────────────────────────────

@router.get("/improve")
async def suggest_prompt_improvements():
    """
    Ask Opus 4.6 to analyze the current prompt's performance and suggest edits.
    Returns structured suggestions for human review — AI never auto-modifies curated prompts.
    """
    suggestions = await _orchestrator.suggest_improvements()
    if not suggestions:
        return {"message": "Cannot analyze — no prompt or no API key."}
    return suggestions


# ─── Performance metrics ──────────────────────────────────────────

@router.get("/performance")
async def get_prompt_performance():
    """Get performance metrics for the active prompt."""
    entry = get_prompt(ACTIVE_DOMAINS)
    if not entry:
        return {"message": "No prompt exists yet."}

    perf = entry.get("performance", {})
    return {
        "key": entry["key"],
        "status": entry["status"],
        "version": entry["version"],
        "performance": perf,
        "health": _assess_health(perf),
    }


def _assess_health(perf: dict) -> dict:
    """Assess prompt health from performance metrics."""
    runs = perf.get("runs", 0)
    if runs == 0:
        return {"grade": "new", "message": "No runs yet."}

    avg_conf = perf.get("avg_confidence", 0)
    conflict_rate = perf.get("conflicts_detected", 0) / max(runs, 1)
    regime_change_rate = perf.get("regime_changes", 0) / max(runs, 1)

    issues = []
    if avg_conf < 0.4:
        issues.append("Low confidence — prompt may be too vague")
    if conflict_rate > 0.5:
        issues.append("High conflict rate — agents frequently disagree")
    if regime_change_rate > 0.3:
        issues.append("Frequent regime changes — possible noise")

    if not issues:
        grade = "healthy"
    elif len(issues) == 1:
        grade = "needs_attention"
    else:
        grade = "needs_review"

    return {
        "grade": grade,
        "avg_confidence": round(avg_conf, 3),
        "conflict_rate": round(conflict_rate, 3),
        "regime_change_rate": round(regime_change_rate, 3),
        "issues": issues,
        "recommendation": (
            "Consider running /api/prompts/improve for AI suggestions"
            if issues else "Prompt is performing well"
        ),
    }


# ─── Reset (force re-bootstrap) ──────────────────────────────────

@router.post("/reset")
async def reset_prompt():
    """Delete the active prompt. Next synthesis run will bootstrap a fresh one."""
    deleted = delete_prompt(ACTIVE_DOMAINS)
    return {
        "deleted": deleted,
        "message": "Prompt deleted. Next synthesis run will auto-generate a new one." if deleted else "No prompt found to delete.",
    }
