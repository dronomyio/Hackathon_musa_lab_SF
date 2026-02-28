"""Inflation Expectations Agent — breakeven analysis and real yield regime."""

from agents.base_agent import BaseAgent, AgentSignal


class InflationAgent(BaseAgent):
    name = "inflation_expectations"

    def analyze(self, data: dict[str, list[dict]]) -> AgentSignal:
        t5yie = data.get("T5YIE", [])
        t10yie = data.get("T10YIE", [])
        t5yifr = data.get("T5YIFR", [])
        dfii10 = data.get("DFII10", [])
        dgs10 = data.get("DGS10", [])

        metrics = {}
        summaries = []
        signal = "neutral"
        confidence = 0.5
        regime = "anchored"

        # ── 10Y Breakeven ────────────────────────────────────────────
        if t10yie:
            be10 = self.last_value(t10yie)
            be10_prev = self.last_value(t10yie, 22)
            if be10 is not None:
                metrics["breakeven_10y"] = round(be10, 3)
                hist = self.values(t10yie)
                metrics["be10_percentile"] = round(
                    self.percentile_rank(be10, hist), 1
                )
                if be10_prev:
                    metrics["be10_30d_change"] = round(be10 - be10_prev, 3)

                if be10 > 2.8:
                    regime = "unanchored_high"
                    signal = "bearish"
                    confidence = 0.8
                    summaries.append(
                        f"10Y breakeven at {be10:.2f}% — inflation expectations elevated."
                    )
                elif be10 > 2.4:
                    regime = "drifting"
                    signal = "caution"
                    confidence = 0.6
                    summaries.append(
                        f"10Y breakeven at {be10:.2f}% — above Fed target, drifting."
                    )
                elif be10 < 1.5:
                    regime = "deflationary"
                    signal = "caution"
                    confidence = 0.7
                    summaries.append(
                        f"10Y breakeven at {be10:.2f}% — deflationary expectations."
                    )
                else:
                    summaries.append(
                        f"10Y breakeven at {be10:.2f}% — well anchored near 2% target."
                    )
                    signal = "bullish"
                    confidence = 0.65

        # ── 5Y Breakeven ─────────────────────────────────────────────
        if t5yie:
            be5 = self.last_value(t5yie)
            if be5 is not None:
                metrics["breakeven_5y"] = round(be5, 3)

        # ── 5Y5Y Forward ─────────────────────────────────────────────
        if t5yifr:
            fwd = self.last_value(t5yifr)
            if fwd is not None:
                metrics["forward_5y5y"] = round(fwd, 3)
                if fwd > 2.6:
                    summaries.append(
                        f"5Y5Y forward at {fwd:.2f}% — long-term expectations rising."
                    )
                elif fwd < 1.8:
                    summaries.append(
                        f"5Y5Y forward at {fwd:.2f}% — long-term disinflation priced."
                    )

        # ── Real yield ───────────────────────────────────────────────
        if dfii10:
            real10 = self.last_value(dfii10)
            if real10 is not None:
                metrics["real_yield_10y"] = round(real10, 3)
                if real10 > 2.5:
                    summaries.append(
                        f"10Y real yield at {real10:.2f}% — restrictive territory."
                    )
                elif real10 > 1.5:
                    summaries.append(
                        f"10Y real yield at {real10:.2f}% — moderately positive."
                    )
                elif real10 < 0:
                    summaries.append(
                        f"10Y real yield at {real10:.2f}% — negative, accommodative."
                    )

        # ── Nominal-Real decomposition ───────────────────────────────
        if dgs10 and dfii10:
            nom = self.last_value(dgs10)
            real = self.last_value(dfii10)
            if nom is not None and real is not None:
                implied_be = nom - real
                metrics["implied_breakeven"] = round(implied_be, 3)

        return AgentSignal(
            agent_name=self.name,
            regime=regime,
            signal=signal,
            confidence=round(confidence, 2),
            summary=" ".join(summaries) if summaries else "Insufficient inflation data.",
            metrics=metrics,
            details={"latest_date": self.last_date(t10yie) or self.last_date(dfii10)},
        )
