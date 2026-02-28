"""Tail Risk Agent — long-duration bond and term premium analysis."""

from agents.base_agent import BaseAgent, AgentSignal


class TailRiskAgent(BaseAgent):
    name = "tail_risk"

    def analyze(self, data: dict[str, list[dict]]) -> AgentSignal:
        dgs10 = data.get("DGS10", [])
        dgs20 = data.get("DGS20", [])
        dgs30 = data.get("DGS30", [])

        metrics = {}
        summaries = []
        signal = "neutral"
        confidence = 0.5
        regime = "normal"

        y10 = self.last_value(dgs10)
        y20 = self.last_value(dgs20)
        y30 = self.last_value(dgs30)

        if any(v is None for v in [y10, y30]):
            return AgentSignal(
                agent_name=self.name, regime="unknown", signal="neutral",
                confidence=0.0, summary="Insufficient long-bond data.",
            )

        # ── 30Y-10Y spread (term premium proxy) ─────────────────────
        tail_spread = y30 - y10
        metrics["yield_10y"] = round(y10, 3)
        metrics["yield_20y"] = round(y20, 3) if y20 else None
        metrics["yield_30y"] = round(y30, 3)
        metrics["spread_30y_10y"] = round(tail_spread, 3)

        # Historical context
        if dgs30 and dgs10:
            aligned = self.align_series(dgs10, dgs30)
            hist_spread = [
                aligned["series"][1][i] - aligned["series"][0][i]
                for i in range(len(aligned["dates"]))
            ]
            if hist_spread:
                metrics["tail_spread_percentile"] = round(
                    self.percentile_rank(tail_spread, hist_spread), 1
                )
                metrics["tail_spread_mean"] = round(
                    sum(hist_spread) / len(hist_spread), 3
                )

        # ── 30d change ───────────────────────────────────────────────
        y30_prev = self.last_value(dgs30, 22)
        y10_prev = self.last_value(dgs10, 22)
        if y30_prev and y10_prev:
            prev_spread = y30_prev - y10_prev
            metrics["tail_spread_30d_change"] = round(tail_spread - prev_spread, 3)

        # ── 20Y-30Y segment (ultra-long) ─────────────────────────────
        if y20:
            ultra_spread = y30 - y20
            metrics["spread_30y_20y"] = round(ultra_spread, 3)
            if ultra_spread < -0.05:
                summaries.append(
                    f"30Y-20Y inverted ({ultra_spread:.2f}%) — unusual, "
                    "possibly pension/insurance demand compressing ultra-long."
                )

        # ── Regime classification ────────────────────────────────────
        if tail_spread > 0.4:
            regime = "steep_tail"
            signal = "caution"
            confidence = 0.7
            summaries.append(
                f"30Y-10Y at {tail_spread:.2f}% — significant term premium. "
                "Duration risk elevated. Fiscal concerns may be driving long-end supply fears."
            )
        elif tail_spread > 0.15:
            regime = "normal_tail"
            signal = "bullish"
            confidence = 0.6
            summaries.append(
                f"30Y-10Y at {tail_spread:.2f}% — healthy term premium. "
                "Market fairly compensating duration risk."
            )
        elif tail_spread > 0:
            regime = "flat_tail"
            signal = "neutral"
            confidence = 0.55
            summaries.append(
                f"30Y-10Y at {tail_spread:.2f}% — compressed. "
                "Possible expectations of lower long-run rates or convexity bid."
            )
        else:
            regime = "inverted_tail"
            signal = "bearish"
            confidence = 0.75
            summaries.append(
                f"30Y-10Y inverted at {tail_spread:.2f}% — "
                "extreme long-end demand or deep recession pricing."
            )

        # ── Absolute level context ───────────────────────────────────
        if y30 > 5.0:
            summaries.append(
                f"30Y at {y30:.2f}% — multi-decade high territory. "
                "Significant headwind for mortgages and long-duration assets."
            )
        elif y30 < 3.5:
            summaries.append(
                f"30Y at {y30:.2f}% — historically low, favorable for borrowers."
            )

        return AgentSignal(
            agent_name=self.name,
            regime=regime,
            signal=signal,
            confidence=round(confidence, 2),
            summary=" ".join(summaries),
            metrics=metrics,
            details={"latest_date": self.last_date(dgs30)},
        )
