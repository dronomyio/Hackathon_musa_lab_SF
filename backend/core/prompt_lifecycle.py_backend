"""
Prompt Lifecycle Manager — Curated system prompts with human-in-the-loop.

Flow:
  1. User request comes in → check if a curated prompt exists for this domain combo
  2. If YES → use it (human-verified, battle-tested)
  3. If NO → Opus 4.6 auto-generates one → marks as DRAFT
  4. DRAFT prompts get used but flagged for human review
  5. Human reviews, edits, approves → becomes CURATED
  6. Every synthesis run logs performance → prompts evolve over time
  7. Prompts are versioned — can roll back to any previous version

Storage: JSON file on disk (simple, portable, no DB dependency)
Location: /app/data/prompt_library.json (persists across Docker restarts via volume)
"""

import json
import hashlib
import os
from datetime import datetime
from typing import Optional
from pathlib import Path


LIBRARY_PATH = os.environ.get(
    "PROMPT_LIBRARY_PATH",
    "/app/data/prompt_library.json"
)


def _load_library() -> dict:
    """Load the prompt library from disk."""
    path = Path(LIBRARY_PATH)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"prompts": {}, "metadata": {"created": datetime.now().isoformat()}}


def _save_library(lib: dict):
    """Save the prompt library to disk."""
    path = Path(LIBRARY_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(lib, f, indent=2, default=str)


def _domain_key(domains: list[str]) -> str:
    """Generate a stable key from a sorted list of domain names."""
    normalized = sorted(d.strip().lower().replace(" ", "_") for d in domains)
    return hashlib.md5("|".join(normalized).encode()).hexdigest()[:12]


# ═══════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════

def get_prompt(domains: list[str]) -> Optional[dict]:
    """
    Look up a curated or draft prompt for the given domain combination.

    Returns:
        {
            "key": "abc123",
            "status": "curated" | "draft" | "evolving",
            "system_prompt": "...",
            "version": 3,
            "domains": ["housing", "commodities"],
            "user_intent": "monitor housing for DeFi yield risk",
            "created_at": "2026-02-24T...",
            "curated_at": "2026-02-25T..." | null,
            "curated_by": "suvasis" | null,
            "performance": { "runs": 45, "avg_confidence": 0.72, ... },
            "history": [ previous versions ]
        }
    or None if no prompt exists for this domain combo.
    """
    lib = _load_library()
    key = _domain_key(domains)
    return lib["prompts"].get(key)


def get_best_prompt(domains: list[str]) -> Optional[str]:
    """Get just the system prompt text, preferring curated over draft."""
    entry = get_prompt(domains)
    if not entry:
        return None

    # Prefer curated, then evolving, then draft
    if entry["status"] == "curated":
        return entry["system_prompt"]
    elif entry["status"] == "evolving":
        return entry["system_prompt"]
    elif entry["status"] == "draft":
        return entry["system_prompt"]
    return None


def save_draft(
    domains: list[str],
    system_prompt: str,
    user_intent: str,
    generated_by: str = "auto",
) -> dict:
    """
    Save an auto-generated prompt as DRAFT, pending human review.

    If a prompt already exists for this domain combo:
      - If it's curated → DON'T overwrite, return existing
      - If it's draft → overwrite with new version
    """
    lib = _load_library()
    key = _domain_key(domains)

    existing = lib["prompts"].get(key)

    # Never overwrite a curated prompt automatically
    if existing and existing["status"] == "curated":
        return existing

    version = (existing["version"] + 1) if existing else 1
    history = existing.get("history", []) if existing else []

    # Archive current version before overwriting
    if existing:
        history.append({
            "version": existing["version"],
            "system_prompt": existing["system_prompt"],
            "status": existing["status"],
            "saved_at": datetime.now().isoformat(),
        })
        # Keep last 10 versions
        history = history[-10:]

    entry = {
        "key": key,
        "status": "draft",
        "system_prompt": system_prompt,
        "version": version,
        "domains": sorted(domains),
        "user_intent": user_intent,
        "generated_by": generated_by,
        "created_at": existing["created_at"] if existing else datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "curated_at": None,
        "curated_by": None,
        "performance": (existing or {}).get("performance", {
            "runs": 0,
            "avg_confidence": 0.0,
            "regime_changes": 0,
            "conflicts_detected": 0,
            "last_run": None,
        }),
        "human_notes": (existing or {}).get("human_notes", ""),
        "history": history,
    }

    lib["prompts"][key] = entry
    _save_library(lib)
    return entry


def curate_prompt(
    domains: list[str],
    edited_prompt: Optional[str] = None,
    curator: str = "human",
    notes: str = "",
) -> dict:
    """
    Human approves (and optionally edits) a prompt → status becomes CURATED.

    Args:
        domains: domain list to identify which prompt
        edited_prompt: if provided, replaces the system prompt text
        curator: who approved it
        notes: human notes about what was changed and why
    """
    lib = _load_library()
    key = _domain_key(domains)
    entry = lib["prompts"].get(key)

    if not entry:
        raise ValueError(f"No prompt found for domains: {domains}")

    # Archive current before curating
    entry.setdefault("history", []).append({
        "version": entry["version"],
        "system_prompt": entry["system_prompt"],
        "status": entry["status"],
        "saved_at": datetime.now().isoformat(),
    })
    entry["history"] = entry["history"][-10:]

    if edited_prompt:
        entry["system_prompt"] = edited_prompt

    entry["status"] = "curated"
    entry["version"] += 1
    entry["curated_at"] = datetime.now().isoformat()
    entry["curated_by"] = curator
    entry["updated_at"] = datetime.now().isoformat()
    entry["human_notes"] = notes if notes else entry.get("human_notes", "")

    lib["prompts"][key] = entry
    _save_library(lib)
    return entry


def log_run(domains: list[str], confidence: float, regime: str, conflicts: list):
    """
    Log a synthesis run's performance against the prompt.
    Called after every AgentLoop cycle to track prompt effectiveness.
    """
    lib = _load_library()
    key = _domain_key(domains)
    entry = lib["prompts"].get(key)
    if not entry:
        return

    perf = entry.get("performance", {
        "runs": 0, "avg_confidence": 0.0,
        "regime_changes": 0, "conflicts_detected": 0,
        "last_run": None, "last_regime": None,
    })

    perf["runs"] += 1

    # Running average of confidence
    n = perf["runs"]
    perf["avg_confidence"] = ((perf["avg_confidence"] * (n - 1)) + confidence) / n

    # Track regime changes
    if perf.get("last_regime") and perf["last_regime"] != regime:
        perf["regime_changes"] += 1
    perf["last_regime"] = regime

    # Track conflicts
    if conflicts:
        perf["conflicts_detected"] += 1

    perf["last_run"] = datetime.now().isoformat()

    # Auto-evolve: if draft has 20+ successful runs with avg confidence > 0.6,
    # promote to "evolving" (good enough to use, but still benefits from human review)
    if entry["status"] == "draft" and perf["runs"] >= 20 and perf["avg_confidence"] > 0.6:
        entry["status"] = "evolving"

    entry["performance"] = perf
    lib["prompts"][key] = entry
    _save_library(lib)


def list_prompts(status: Optional[str] = None) -> list[dict]:
    """List all prompts, optionally filtered by status."""
    lib = _load_library()
    prompts = list(lib["prompts"].values())
    if status:
        prompts = [p for p in prompts if p["status"] == status]
    return sorted(prompts, key=lambda p: p.get("updated_at", ""), reverse=True)


def rollback(domains: list[str], to_version: int) -> dict:
    """Roll back a prompt to a previous version."""
    lib = _load_library()
    key = _domain_key(domains)
    entry = lib["prompts"].get(key)
    if not entry:
        raise ValueError(f"No prompt found for domains: {domains}")

    target = None
    for h in entry.get("history", []):
        if h["version"] == to_version:
            target = h
            break

    if not target:
        raise ValueError(f"Version {to_version} not found in history")

    # Archive current
    entry["history"].append({
        "version": entry["version"],
        "system_prompt": entry["system_prompt"],
        "status": entry["status"],
        "saved_at": datetime.now().isoformat(),
    })

    entry["system_prompt"] = target["system_prompt"]
    entry["version"] += 1
    entry["status"] = target.get("status", "draft")
    entry["updated_at"] = datetime.now().isoformat()

    lib["prompts"][key] = entry
    _save_library(lib)
    return entry


def delete_prompt(domains: list[str]) -> bool:
    """Delete a prompt entry."""
    lib = _load_library()
    key = _domain_key(domains)
    if key in lib["prompts"]:
        del lib["prompts"][key]
        _save_library(lib)
        return True
    return False
