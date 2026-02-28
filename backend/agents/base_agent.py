"""Base agent class for bond market analysis."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
import math


@dataclass
class AgentSignal:
    """Output from an agent's analysis."""

    agent_name: str
    regime: str
    signal: str  # "bullish", "bearish", "caution", "neutral"
    confidence: float  # 0.0 to 1.0
    summary: str
    details: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    timestamp: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "regime": self.regime,
            "signal": self.signal,
            "confidence": self.confidence,
            "summary": self.summary,
            "details": self.details,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
        }


class BaseAgent(ABC):
    """Abstract base for all inference agents."""

    name: str = "base"

    @abstractmethod
    def analyze(self, data: dict[str, list[dict]]) -> AgentSignal:
        """Run analysis and return a signal."""
        ...

    # ── Utility methods ──────────────────────────────────────────────

    @staticmethod
    def last_value(series: list[dict], offset: int = 0) -> Optional[float]:
        if not series or len(series) <= offset:
            return None
        return series[-(1 + offset)]["value"]

    @staticmethod
    def last_date(series: list[dict]) -> Optional[str]:
        if not series:
            return None
        return series[-1]["date"]

    @staticmethod
    def values(series: list[dict]) -> list[float]:
        return [o["value"] for o in series]

    @staticmethod
    def dates(series: list[dict]) -> list[str]:
        return [o["date"] for o in series]

    @staticmethod
    def daily_changes(values: list[float]) -> list[float]:
        return [values[i] - values[i - 1] for i in range(1, len(values))]

    @staticmethod
    def rolling_mean(values: list[float], window: int) -> list[float]:
        result = []
        for i in range(window - 1, len(values)):
            result.append(sum(values[i - window + 1 : i + 1]) / window)
        return result

    @staticmethod
    def pearson_correlation(x: list[float], y: list[float]) -> float:
        """Compute Pearson correlation between two series."""
        n = min(len(x), len(y))
        if n < 3:
            return 0.0
        x, y = x[:n], y[:n]
        mx = sum(x) / n
        my = sum(y) / n
        num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
        dx = sum((xi - mx) ** 2 for xi in x)
        dy = sum((yi - my) ** 2 for yi in y)
        denom = math.sqrt(dx * dy)
        return num / denom if denom > 0 else 0.0

    @staticmethod
    def rolling_correlation(
        x: list[float], y: list[float], window: int = 30
    ) -> tuple[list[float], list[str]]:
        """Rolling window Pearson correlation on daily changes."""
        dx = [x[i] - x[i - 1] for i in range(1, len(x))]
        dy = [y[i] - y[i - 1] for i in range(1, len(y))]
        n = min(len(dx), len(dy))
        dx, dy = dx[:n], dy[:n]

        corrs = []
        for i in range(window, n):
            sx = dx[i - window : i]
            sy = dy[i - window : i]
            mx = sum(sx) / window
            my_ = sum(sy) / window
            num = sum((a - mx) * (b - my_) for a, b in zip(sx, sy))
            ddx = sum((a - mx) ** 2 for a in sx)
            ddy = sum((b - my_) ** 2 for b in sy)
            denom = math.sqrt(ddx * ddy)
            corrs.append(num / denom if denom > 0 else 0.0)

        return corrs

    @staticmethod
    def align_series(*series_list: list[dict]) -> dict:
        """Align multiple series to common dates."""
        date_sets = [set(o["date"] for o in s) for s in series_list]
        common = sorted(set.intersection(*date_sets))
        result = {"dates": common, "series": []}
        for s in series_list:
            lookup = {o["date"]: o["value"] for o in s}
            result["series"].append([lookup[d] for d in common])
        return result

    @staticmethod
    def percentile_rank(value: float, history: list[float]) -> float:
        """Where does value sit in the historical distribution? 0-100."""
        if not history:
            return 50.0
        below = sum(1 for v in history if v < value)
        return (below / len(history)) * 100
