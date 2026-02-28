"""
Employment & Financial Stress Agent — Leads Fed decisions by 30-60 days.

Jobless claims (weekly): most timely recession indicator.
Unemployment rate: rising → rate cuts → bullish crypto.
Financial Stress indices: composite risk-off signal.
These indicators predict the Fed's next move, which drives crypto 60% of the time.
"""

from agents.base_agent import BaseAgent, AgentSignal


class EmploymentStressAgent(BaseAgent):
    name = "employment_stress"

    def analyze(self, data: dict[str, list[dict]]) -> AgentSignal:
        icsa = data.get("ICSA", [])        # weekly initial claims
        ccsa = data.get("CCSA", [])        # continued claims
        unrate = data.get("UNRATE", [])     # monthly unemployment
        stlfsi = data.get("STLFSI4", [])   # stress index
        nfci = data.get("NFCI", [])        # financial conditions

        metrics = {}
        signals = []

        # ── Initial Jobless Claims (weekly — most timely) ────────
        if len(icsa) >= 5:
            claims_now = self.last_value(icsa)
            claims_4w_ago = self.last_value(icsa, 3) if len(icsa) >= 4 else None

            if claims_now:
                metrics["initial_claims"] = round(claims_now)
                if claims_4w_ago:
                    claims_trend = claims_now - claims_4w_ago
                    metrics["claims_4w_trend"] = round(claims_trend)

                    # 4-week moving average
                    recent = [self.last_value(icsa, i) for i in range(4) if self.last_value(icsa, i)]
                    if recent:
                        metrics["claims_4w_avg"] = round(sum(recent) / len(recent))

                # Thresholds
                if claims_now > 300000:
                    signals.append(("bearish", 0.8, f"Claims at {claims_now/1000:.0f}K — recession territory"))
                elif claims_now > 250000:
                    signals.append(("caution", 0.6, f"Claims rising to {claims_now/1000:.0f}K — labor softening"))
                elif claims_now < 200000:
                    signals.append(("bullish", 0.5, f"Claims at {claims_now/1000:.0f}K — tight labor, no recession"))
                else:
                    signals.append(("neutral", 0.4, f"Claims at {claims_now/1000:.0f}K — normal range"))

        # ── Continued Claims ─────────────────────────────────────
        if len(ccsa) >= 2:
            cc_now = self.last_value(ccsa)
            if cc_now:
                metrics["continued_claims"] = round(cc_now)
                if cc_now > 2000000:
                    signals.append(("bearish", 0.6, "Continued claims >2M — difficulty finding work"))

        # ── Unemployment Rate (monthly) ──────────────────────────
        if len(unrate) >= 2:
            ur_now = self.last_value(unrate)
            ur_prev = self.last_value(unrate, 1)
            ur_12m = self.last_value(unrate, 12) if len(unrate) >= 13 else None

            if ur_now:
                metrics["unemployment_rate"] = round(ur_now, 1)
                if ur_prev:
                    metrics["unemployment_mom_change"] = round(ur_now - ur_prev, 2)

                if ur_12m:
                    ur_yoy = ur_now - ur_12m
                    metrics["unemployment_yoy_change"] = round(ur_yoy, 2)
                    # Sahm Rule: if 3-month avg rises 0.5% from 12-month low → recession
                    if ur_yoy > 0.5:
                        signals.append(("bearish", 0.8, f"Unemployment up {ur_yoy:.1f}pp YoY — Sahm Rule flashing"))
                    elif ur_yoy > 0.2:
                        signals.append(("caution", 0.6, "Unemployment drifting higher"))

                # Fed pivot signal
                if ur_now > 4.5:
                    signals.append(("bullish", 0.5, f"Unemployment at {ur_now}% — Fed cuts likely → crypto bullish"))

        # ── Financial Stress Index ───────────────────────────────
        if len(stlfsi) >= 2:
            stress = self.last_value(stlfsi)
            stress_prev = self.last_value(stlfsi, 4) if len(stlfsi) >= 5 else None

            if stress is not None:
                metrics["financial_stress_idx"] = round(stress, 3)
                if stress_prev is not None:
                    metrics["stress_4w_change"] = round(stress - stress_prev, 3)

                # STLFSI: 0 = average, positive = above-average stress
                if stress > 1.0:
                    signals.append(("bearish", 0.8, f"Financial stress elevated ({stress:.2f}) — systemic risk"))
                elif stress > 0.5:
                    signals.append(("caution", 0.6, "Financial stress above average"))
                elif stress < -0.5:
                    signals.append(("bullish", 0.5, "Financial conditions very loose"))

        # ── NFCI ─────────────────────────────────────────────────
        if len(nfci) >= 2:
            nfci_now = self.last_value(nfci)
            if nfci_now is not None:
                metrics["nfci"] = round(nfci_now, 3)
                # NFCI: 0 = average, positive = tighter than average
                if nfci_now > 0.5:
                    signals.append(("bearish", 0.6, "Financial conditions tightening"))
                elif nfci_now < -0.5:
                    signals.append(("bullish", 0.5, "Financial conditions very accommodative"))

        # ── Synthesize ───────────────────────────────────────────
        if not signals:
            return AgentSignal(
                agent_name=self.name, regime="unknown", signal="neutral",
                confidence=0.3, summary="Insufficient employment/stress data.",
                metrics=metrics,
            )

        bullish = sum(c for s, c, _ in signals if s == "bullish")
        bearish = sum(c for s, c, _ in signals if s in ("bearish", "caution"))
        total = sum(c for _, c, _ in signals)

        if bearish > bullish * 2:
            regime, signal = "deteriorating", "bearish"
        elif bearish > bullish * 1.3:
            regime, signal = "softening", "caution"
        elif bullish > bearish * 1.5:
            regime, signal = "strong_dovish_pivot", "bullish"
        else:
            regime, signal = "stable", "neutral"

        conf = min(0.9, total / (len(signals) * 0.8))

        return AgentSignal(
            agent_name=self.name,
            regime=regime,
            signal=signal,
            confidence=round(conf, 2),
            summary=". ".join(s for _, _, s in signals[:3]),
            details={"regime_label": regime.replace("_", " ").title()},
            metrics=metrics,
        )
