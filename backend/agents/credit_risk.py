"""Credit Risk Agent — monitors corporate spreads and risk appetite."""

from agents.base_agent import BaseAgent, AgentSignal


class CreditRiskAgent(BaseAgent):
    name = "credit_risk"

    def analyze(self, data: dict[str, list[dict]]) -> AgentSignal:
        aaa = data.get("AAA", [])
        baa = data.get("BAA", [])
        baa10y = data.get("BAA10Y", [])
        hy_oas = data.get("BAMLH0A0HYM2", [])
        ig_oas = data.get("BAMLC0A0CM", [])

        metrics = {}
        signal = "neutral"
        confidence = 0.5
        regime = "normal"
        summaries = []

        # ── Aaa-Baa spread (default risk) ────────────────────────────
        if aaa and baa:
            aaa_now = self.last_value(aaa)
            baa_now = self.last_value(baa)
            if aaa_now is not None and baa_now is not None:
                credit_spread = baa_now - aaa_now
                metrics["aaa_yield"] = round(aaa_now, 3)
                metrics["baa_yield"] = round(baa_now, 3)
                metrics["baa_aaa_spread"] = round(credit_spread, 3)

                # Historical context
                hist_spread = [
                    b["value"] - a["value"]
                    for a, b in zip(aaa, baa)
                    if a["date"] == b["date"]
                ]
                if hist_spread:
                    metrics["spread_percentile"] = round(
                        self.percentile_rank(credit_spread, hist_spread), 1
                    )

                if credit_spread > 1.5:
                    regime = "stress"
                    signal = "bearish"
                    confidence = 0.8
                    summaries.append(
                        f"Baa-Aaa spread at {credit_spread:.2f}% — elevated credit stress."
                    )
                elif credit_spread > 1.0:
                    regime = "widening"
                    signal = "caution"
                    confidence = 0.65
                    summaries.append(
                        f"Baa-Aaa spread at {credit_spread:.2f}% — widening, monitor closely."
                    )
                else:
                    summaries.append(
                        f"Baa-Aaa spread at {credit_spread:.2f}% — tight, risk appetite healthy."
                    )

        # ── Baa over 10Y Treasury ────────────────────────────────────
        if baa10y:
            baa10y_now = self.last_value(baa10y)
            if baa10y_now is not None:
                metrics["baa_10y_spread"] = round(baa10y_now, 3)
                hist = self.values(baa10y)
                metrics["baa_10y_percentile"] = round(
                    self.percentile_rank(baa10y_now, hist), 1
                )

                if baa10y_now > 3.0:
                    regime = "stress"
                    signal = "bearish"
                    confidence = max(confidence, 0.8)
                    summaries.append(
                        f"Baa-10Y at {baa10y_now:.2f}% — flight to quality active."
                    )

        # ── High Yield OAS ───────────────────────────────────────────
        if hy_oas:
            hy_now = self.last_value(hy_oas)
            hy_prev = self.last_value(hy_oas, 22)
            if hy_now is not None:
                metrics["hy_oas"] = round(hy_now, 3)
                if hy_prev:
                    metrics["hy_oas_30d_change"] = round(hy_now - hy_prev, 3)

                hist = self.values(hy_oas)
                metrics["hy_oas_percentile"] = round(
                    self.percentile_rank(hy_now, hist), 1
                )

                if hy_now > 500:  # 500 bps
                    summaries.append(
                        f"HY OAS at {hy_now:.0f} bps — distressed territory."
                    )
                    signal = "bearish"
                    confidence = max(confidence, 0.85)
                elif hy_now > 400:
                    summaries.append(f"HY OAS at {hy_now:.0f} bps — elevated.")
                    if signal != "bearish":
                        signal = "caution"
                else:
                    summaries.append(
                        f"HY OAS at {hy_now:.0f} bps — benign conditions."
                    )

        # ── IG OAS ───────────────────────────────────────────────────
        if ig_oas:
            ig_now = self.last_value(ig_oas)
            if ig_now is not None:
                metrics["ig_oas"] = round(ig_now, 3)

        if signal == "neutral" and regime == "normal":
            signal = "bullish"
            confidence = 0.6

        return AgentSignal(
            agent_name=self.name,
            regime=regime,
            signal=signal,
            confidence=round(confidence, 2),
            summary=" ".join(summaries) if summaries else "Insufficient credit data.",
            metrics=metrics,
            details={"latest_date": self.last_date(baa) or self.last_date(aaa)},
        )
