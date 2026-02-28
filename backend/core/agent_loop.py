"""
AgentLoop — Background scheduler for continuous bond market monitoring.

Runs the full agent pipeline (FRED fetch → sub-agents → Opus 4.6 synthesis)
on a configurable interval. Caches the latest result for instant API responses.

Supports:
  - Configurable interval (default 15 min)
  - Immediate first run on startup
  - WebSocket broadcast to connected dashboard clients
  - Health tracking (last run, next run, consecutive failures)
  - Graceful shutdown
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from core.config import get_settings
from core.fred_client import FREDClient
from data.series_config import EXTENDED_SERIES_IDS
from agents.orchestrator import OrchestratorAgent

logger = logging.getLogger("agent_loop")


class AgentLoop:
    """Background agent execution loop."""

    def __init__(
        self,
        fred_client: FREDClient,
        orchestrator: OrchestratorAgent,
        interval_seconds: int = 900,  # 15 min default
    ):
        self.fred_client = fred_client
        self.orchestrator = orchestrator
        self.interval = interval_seconds

        # State
        self._latest_result: Optional[dict] = None
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._run_count = 0
        self._consecutive_failures = 0
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None
        self._last_error: Optional[str] = None

        # WebSocket subscribers
        self._subscribers: set[asyncio.Queue] = set()

    # ─── Lifecycle ───────────────────────────────────────────────────

    def start(self):
        """Start the background loop. Call this from FastAPI lifespan."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"AgentLoop started — interval={self.interval}s")

    async def stop(self):
        """Graceful shutdown."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AgentLoop stopped")

    # ─── Main loop ───────────────────────────────────────────────────

    async def _loop(self):
        """Run agents on interval forever."""
        # Immediate first run
        await self._execute()

        while self._running:
            self._next_run = datetime.now() + timedelta(seconds=self.interval)
            try:
                await asyncio.sleep(self.interval)
                if self._running:
                    await self._execute()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"AgentLoop iteration error: {e}")
                self._consecutive_failures += 1
                self._last_error = str(e)
                # Backoff on repeated failures (max 5 min extra)
                backoff = min(300, self._consecutive_failures * 30)
                await asyncio.sleep(backoff)

    async def _execute(self):
        """Single execution: fetch data → run agents → cache → broadcast."""
        start = datetime.now()
        logger.info(f"AgentLoop executing (run #{self._run_count + 1})...")

        try:
            # Force fresh data from FRED
            data = await self.fred_client.fetch_multiple(
                EXTENDED_SERIES_IDS, force=True
            )

            series_count = len([k for k, v in data.items() if v])
            logger.info(f"  Fetched {series_count}/{len(EXTENDED_SERIES_IDS)} series")

            if series_count == 0:
                raise RuntimeError("No series data returned from FRED")

            # Run orchestrator (sub-agents + Claude/fallback synthesis)
            result = await self.orchestrator.run_all(data)

            # Attach loop metadata
            elapsed = (datetime.now() - start).total_seconds()
            result["_loop"] = {
                "run_number": self._run_count + 1,
                "elapsed_seconds": round(elapsed, 2),
                "engine": result.get("synthesis_engine", "unknown"),
                "series_fetched": series_count,
                "timestamp": datetime.now().isoformat(),
                "interval_seconds": self.interval,
            }

            # Cache
            self._latest_result = result
            self._run_count += 1
            self._consecutive_failures = 0
            self._last_run = datetime.now()
            self._last_error = None

            logger.info(
                f"  Done in {elapsed:.1f}s — regime: "
                f"{result.get('synthesis', {}).get('regime_label', 'unknown')}"
            )

            # Broadcast to WebSocket subscribers
            await self._broadcast(result)

        except Exception as e:
            self._consecutive_failures += 1
            self._last_error = str(e)
            logger.error(f"  Execution failed: {e}")

    # ─── WebSocket pub/sub ───────────────────────────────────────────

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to agent updates. Returns a queue that receives results."""
        q: asyncio.Queue = asyncio.Queue(maxsize=5)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        """Remove a subscriber."""
        self._subscribers.discard(q)

    async def _broadcast(self, result: dict):
        """Push latest result to all connected WebSocket clients."""
        dead = set()
        for q in self._subscribers:
            try:
                # Non-blocking put — drop if client is slow
                q.put_nowait(result)
            except asyncio.QueueFull:
                dead.add(q)

        for q in dead:
            self._subscribers.discard(q)

    # ─── API access ──────────────────────────────────────────────────

    @property
    def latest(self) -> Optional[dict]:
        """Get the most recent agent result (instant, no computation)."""
        return self._latest_result

    @property
    def status(self) -> dict:
        """Loop health status."""
        return {
            "running": self._running,
            "run_count": self._run_count,
            "interval_seconds": self.interval,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self._next_run.isoformat() if self._next_run else None,
            "consecutive_failures": self._consecutive_failures,
            "last_error": self._last_error,
            "subscribers": len(self._subscribers),
            "has_result": self._latest_result is not None,
        }

    async def run_now(self) -> dict:
        """Force an immediate execution outside the scheduled interval."""
        await self._execute()
        return self._latest_result or {"error": "Execution produced no result"}
