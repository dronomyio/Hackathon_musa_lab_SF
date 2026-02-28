"""Cross-Correlation Agent — detects regime divergence between maturities."""

from agents.base_agent import BaseAgent, AgentSignal


class CrossCorrelationAgent(BaseAgent):
    name = "cross_correlation"

    def analyze(self, data: dict[str, list[dict]], window: int = 30) -> AgentSignal:
        dgs2 = data.get("DGS2", [])
        dgs10 = data.get("DGS10", [])
        dgs30 = data.get("DGS30", [])

        if not dgs2 or not dgs10:
            return AgentSignal(
                agent_name=self.name, regime="unknown", signal="neutral",
                confidence=0.0, summary="Insufficient data.",
            )

        # ── Align 2Y and 10Y ────────────────────────────────────────
        aligned = self.align_series(dgs2, dgs10)
        vals2 = aligned["series"][0]
        vals10 = aligned["series"][1]
        dates = aligned["dates"]

        # ── Rolling correlation ──────────────────────────────────────
        corr_series = self.rolling_correlation(vals2, vals10, window)

        if not corr_series:
            return AgentSignal(
                agent_name=self.name, regime="unknown", signal="neutral",
                confidence=0.0, summary="Not enough history for correlation.",
            )

        current_corr = corr_series[-1]
        avg_corr = sum(corr_series) / len(corr_series)
        min_corr = min(corr_series)
        max_corr = max(corr_series)

        # Recent trend (last 10 vs prior 10 correlation values)
        if len(corr_series) > 20:
            recent = sum(corr_series[-10:]) / 10
            prior = sum(corr_series[-20:-10]) / 10
            corr_trend = recent - prior
        else:
            corr_trend = 0

        metrics = {
            "correlation_2y_10y": round(current_corr, 3),
            "correlation_avg": round(avg_corr, 3),
            "correlation_min": round(min_corr, 3),
            "correlation_max": round(max_corr, 3),
            "correlation_trend": round(corr_trend, 3),
            "window_days": window,
            "correlation_history_length": len(corr_series),
        }

        # ── 2Y-30Y correlation if available ──────────────────────────
        if dgs30:
            aligned_30 = self.align_series(dgs2, dgs30)
            corr_2_30 = self.rolling_correlation(
                aligned_30["series"][0], aligned_30["series"][1], window
            )
            if corr_2_30:
                metrics["correlation_2y_30y"] = round(corr_2_30[-1], 3)

        # ── 10Y-30Y correlation ──────────────────────────────────────
        if dgs10 and dgs30:
            aligned_1030 = self.align_series(dgs10, dgs30)
            corr_10_30 = self.rolling_correlation(
                aligned_1030["series"][0], aligned_1030["series"][1], window
            )
            if corr_10_30:
                metrics["correlation_10y_30y"] = round(corr_10_30[-1], 3)

        # ── Regime classification ────────────────────────────────────
        if current_corr > 0.7:
            regime = "synchronized"
            signal = "bullish"
            confidence = 0.65
            summary = (
                f"2Y-10Y ρ = {current_corr:.2f} — highly synchronized. "
                "Single macro driver (Fed expectations) dominates both ends. "
                "Low relative-value opportunity in duration trades."
            )
        elif current_corr > 0.3:
            regime = "transitioning"
            signal = "caution"
            confidence = 0.6
            summary = (
                f"2Y-10Y ρ = {current_corr:.2f} — moderate correlation. "
                "Short end follows Fed, long end follows growth/inflation. "
                "Curve trades becoming more interesting."
            )
        elif current_corr > -0.1:
            regime = "divergent"
            signal = "caution"
            confidence = 0.7
            summary = (
                f"2Y-10Y ρ = {current_corr:.2f} — low correlation, regime divergence. "
                "Distinct forces driving front vs back end. "
                "Often precedes major curve regime changes."
            )
        else:
            regime = "anti_correlated"
            signal = "bearish"
            confidence = 0.75
            summary = (
                f"2Y-10Y ρ = {current_corr:.2f} — negatively correlated! "
                "Extremely unusual. Front and back end moving in opposite directions. "
                "Suggests major macro dislocation."
            )

        # Add trend context
        if abs(corr_trend) > 0.1:
            direction = "rising" if corr_trend > 0 else "falling"
            summary += f" Correlation {direction} ({corr_trend:+.2f} over 20d)."

        # ── Provide the full series for charting ─────────────────────
        # Offset dates for correlation series (starts at window index)
        corr_dates = dates[window + 1 :] if len(dates) > window + 1 else dates
        corr_dates = corr_dates[: len(corr_series)]

        return AgentSignal(
            agent_name=self.name,
            regime=regime,
            signal=signal,
            confidence=round(confidence, 2),
            summary=summary,
            metrics=metrics,
            details={
                "correlation_series": [round(c, 3) for c in corr_series],
                "correlation_dates": corr_dates,
                "latest_date": self.last_date(dgs10),
            },
        )
