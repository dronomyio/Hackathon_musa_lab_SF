"""Yield Curve Regime Agent — detects curve shape and transition dynamics."""

from agents.base_agent import BaseAgent, AgentSignal


class YieldCurveAgent(BaseAgent):
    name = "yield_curve"

    REGIMES = {
        "normal_steep": "Normal Steep",
        "normal_flat": "Normal Flat",
        "inverted": "Inverted",
        "bear_steepening": "Bear Steepening",
        "bull_flattening": "Bull Flattening",
        "bear_flattening": "Bear Flattening",
        "bull_steepening": "Bull Steepening",
    }

    def analyze(self, data: dict[str, list[dict]]) -> AgentSignal:
        dgs2 = data.get("DGS2", [])
        dgs10 = data.get("DGS10", [])
        dgs30 = data.get("DGS30", [])
        t10y2y = data.get("T10Y2Y", [])

        spread_now = self.last_value(t10y2y)
        spread_prev_30d = self.last_value(t10y2y, 22) if len(t10y2y) > 22 else None
        y2_now = self.last_value(dgs2)
        y10_now = self.last_value(dgs10)
        y30_now = self.last_value(dgs30)
        y2_prev = self.last_value(dgs2, 22)
        y10_prev = self.last_value(dgs10, 22)

        if any(v is None for v in [spread_now, y2_now, y10_now]):
            return AgentSignal(
                agent_name=self.name,
                regime="unknown",
                signal="neutral",
                confidence=0.0,
                summary="Insufficient data for yield curve analysis.",
            )

        # ── Regime classification ────────────────────────────────────
        regime = self._classify_regime(spread_now, y2_now, y10_now, y2_prev, y10_prev)

        # ── Transition detection ─────────────────────────────────────
        spread_change = spread_now - spread_prev_30d if spread_prev_30d else 0
        transition = self._detect_transition(spread_now, spread_change)

        # ── Signal ───────────────────────────────────────────────────
        if spread_now < -0.2:
            signal = "bearish"
            confidence = min(0.95, 0.7 + abs(spread_now) * 0.2)
        elif spread_now < 0:
            signal = "bearish"
            confidence = 0.65
        elif spread_now < 0.2:
            signal = "caution"
            confidence = 0.55
        else:
            signal = "bullish"
            confidence = min(0.9, 0.5 + spread_now * 0.15)

        # ── Percentile rank of current spread ────────────────────────
        spread_hist = self.values(t10y2y)
        pct = self.percentile_rank(spread_now, spread_hist)

        # ── Recession probability heuristic ──────────────────────────
        # Sustained inversion (>3 months) is the key signal
        recent_90d = spread_hist[-66:] if len(spread_hist) > 66 else spread_hist
        days_inverted = sum(1 for v in recent_90d if v < 0)
        recession_prob = min(0.85, days_inverted / len(recent_90d)) if recent_90d else 0

        summary = (
            f"10Y−2Y spread at {spread_now:.2f}%. "
            f"Regime: {self.REGIMES.get(regime, regime)}. "
            f"{transition}"
        )

        return AgentSignal(
            agent_name=self.name,
            regime=regime,
            signal=signal,
            confidence=round(confidence, 2),
            summary=summary,
            metrics={
                "spread_10y2y": round(spread_now, 3),
                "spread_30d_change": round(spread_change, 3),
                "spread_percentile": round(pct, 1),
                "yield_2y": round(y2_now, 3),
                "yield_10y": round(y10_now, 3),
                "yield_30y": round(y30_now, 3) if y30_now else None,
                "recession_probability": round(recession_prob, 2),
                "days_inverted_90d": days_inverted,
            },
            details={
                "regime_label": self.REGIMES.get(regime, regime),
                "transition": transition,
                "latest_date": self.last_date(t10y2y),
            },
        )

    def _classify_regime(
        self, spread: float, y2: float, y10: float, y2_prev: float, y10_prev: float
    ) -> str:
        if spread < -0.1:
            return "inverted"

        dy2 = (y2 - y2_prev) if y2_prev else 0
        dy10 = (y10 - y10_prev) if y10_prev else 0

        if dy10 > 0.1 and dy2 < dy10:
            return "bear_steepening"  # Long end rising faster
        if dy2 > 0.1 and dy10 < dy2:
            return "bear_flattening"  # Short end rising faster
        if dy10 < -0.1 and dy2 > dy10:
            return "bull_flattening"  # Long end falling faster
        if dy2 < -0.1 and dy10 > dy2:
            return "bull_steepening"  # Short end falling faster

        if spread > 0.5:
            return "normal_steep"
        return "normal_flat"

    def _detect_transition(self, spread: float, change_30d: float) -> str:
        if change_30d > 0.3:
            return "Rapid steepening — curve normalizing quickly."
        if change_30d > 0.1:
            return "Gradual steepening trend over 30 days."
        if change_30d < -0.3:
            return "Rapid flattening — potential inversion ahead."
        if change_30d < -0.1:
            return "Gradual flattening trend."
        if abs(spread) < 0.1:
            return "Near zero spread — at inflection point."
        return "Stable regime."
