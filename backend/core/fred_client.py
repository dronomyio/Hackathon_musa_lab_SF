"""FRED API client with async fetching and caching."""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional

import httpx

from core.config import get_settings


class Observation:
    __slots__ = ("date", "value")

    def __init__(self, date: str, value: float):
        self.date = date
        self.value = value

    def to_dict(self):
        return {"date": self.date, "value": self.value}


class FREDClient:
    """Async FRED API client with in-memory caching."""

    def __init__(self):
        self.settings = get_settings()
        self._cache: dict[str, list[dict]] = {}
        self._cache_time: Optional[float] = None
        self._fetch_timestamp: Optional[str] = None
        self._errors: list[str] = []

    @property
    def is_cache_valid(self) -> bool:
        if self._cache_time is None:
            return False
        return (time.time() - self._cache_time) < self.settings.cache_ttl_seconds

    async def fetch_series(
        self,
        series_id: str,
        start_date: str,
        end_date: str,
        client: httpx.AsyncClient,
    ) -> list[dict]:
        """Fetch a single series from FRED."""
        params = {
            "series_id": series_id,
            "api_key": self.settings.fred_api_key,
            "file_type": "json",
            "observation_start": start_date,
            "observation_end": end_date,
            "sort_order": "asc",
        }
        try:
            resp = await client.get(
                f"{self.settings.fred_base_url}/series/observations",
                params=params,
                timeout=20.0,
            )
            resp.raise_for_status()
            data = resp.json()
            observations = [
                {"date": o["date"], "value": float(o["value"])}
                for o in data.get("observations", [])
                if o["value"] != "."
            ]
            return observations
        except Exception as e:
            self._errors.append(f"{series_id}: {str(e)}")
            return []

    async def fetch_multiple(
        self, series_ids: list[str], force: bool = False
    ) -> dict[str, list[dict]]:
        """Fetch multiple series concurrently with caching."""
        if self.is_cache_valid and not force:
            # Return cached data for requested series
            return {sid: self._cache.get(sid, []) for sid in series_ids}

        self._errors = []
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (
            datetime.now() - timedelta(days=self.settings.lookback_years * 365)
        ).strftime("%Y-%m-%d")

        results = {}
        async with httpx.AsyncClient() as client:
            # Fetch in batches of 4 to be nice to FRED API
            for i in range(0, len(series_ids), 4):
                batch = series_ids[i : i + 4]
                tasks = [
                    self.fetch_series(sid, start_date, end_date, client)
                    for sid in batch
                ]
                batch_results = await asyncio.gather(*tasks)
                for sid, data in zip(batch, batch_results):
                    results[sid] = data
                if i + 4 < len(series_ids):
                    await asyncio.sleep(0.1)  # Rate limit courtesy

        # Update cache
        self._cache.update(results)
        self._cache_time = time.time()
        self._fetch_timestamp = datetime.now().isoformat()

        return results

    def get_cached(self, series_id: str) -> list[dict]:
        """Get cached data for a series."""
        return self._cache.get(series_id, [])

    @property
    def fetch_timestamp(self) -> Optional[str]:
        return self._fetch_timestamp

    @property
    def errors(self) -> list[str]:
        return self._errors

    def invalidate_cache(self):
        self._cache_time = None
