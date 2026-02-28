"""
Dollar & Volatility Agent — Monitors USD strength and fear gauges.

USD Index: inverse correlation to crypto (strong dollar crushes BTC).
VIX: fear spikes → MEV liquidation cascades, sandwich volume surges.
TED Spread: interbank stress → contagion to crypto.
EUR/USD: global risk sentiment proxy.
"""

from agents.base_agent import BaseAgent, AgentSignal


class DollarVolAgent(BaseAgent):
    name = "dollar_vol"

    def analyze(self, data: dict[str, list[dict]]) -> AgentSignal:
        usd = data.get("DTWEXBGS", [])
        vix = data.get("VIXCLS", [])
        ted = data.get("TEDRATE", [])
        eurusd = data.get("DEXUSEU", [])
        sp500 = data.get("SP500", [])

        metrics = {}
        signals = []

        # ── USD Index ────────────────────────────────────────────
        if len(usd) >= 22:
            usd_now = self.last_value(usd)
            usd_30d = self.last_value(usd, 21)

            if usd_now and usd_30d:
                usd_chg = ((usd_now - usd_30d) / usd_30d) * 100
                metrics["usd_index"] = round(usd_now, 2)
                metrics["usd_30d_change_pct"] = round(usd_chg, 2)

                vals = self.values(usd)
                metrics["usd_percentile"] = round(self.percentile_rank(usd_now, vals), 1)

                if usd_chg > 2:
                    signals.append(("bearish", 0.7, f"USD surging +{usd_chg:.1f}% (30d) — crypto headwind"))
                elif usd_chg < -2:
                    signals.append(("bullish", 0.7, f"USD weakening {usd_chg:.1f}% (30d) — crypto tailwind"))
                else:
                    signals.append(("neutral", 0.4, "USD range-bound"))

        # ── VIX ──────────────────────────────────────────────────
        if len(vix) >= 2:
            vix_now = self.last_value(vix)
            vix_5d = self.last_value(vix, 4) if len(vix) >= 5 else None

            if vix_now:
                metrics["vix"] = round(vix_now, 2)
                if vix_5d:
                    metrics["vix_5d_change"] = round(vix_now - vix_5d, 2)

                vals = self.values(vix)
                metrics["vix_percentile"] = round(self.percentile_rank(vix_now, vals), 1)

                if vix_now > 30:
                    signals.append(("bearish", 0.85, f"VIX at {vix_now:.0f} — panic, liquidation cascades likely"))
                elif vix_now > 22:
                    signals.append(("caution", 0.6, f"VIX elevated at {vix_now:.0f} — risk-off environment"))
                elif vix_now < 14:
                    signals.append(("bullish", 0.6, f"VIX complacent at {vix_now:.0f} — risk-on"))
                else:
                    signals.append(("neutral", 0.4, f"VIX normal at {vix_now:.0f}"))

        # ── TED Spread ───────────────────────────────────────────
        if len(ted) >= 2:
            ted_now = self.last_value(ted)
            if ted_now is not None:
                metrics["ted_spread"] = round(ted_now, 3)
                if ted_now > 0.5:
                    signals.append(("bearish", 0.7, "TED spread elevated — interbank stress, contagion risk"))
                elif ted_now > 0.35:
                    signals.append(("caution", 0.5, "TED spread above normal"))

        # ── EUR/USD ──────────────────────────────────────────────
        if len(eurusd) >= 22:
            eur_now = self.last_value(eurusd)
            eur_30d = self.last_value(eurusd, 21)
            if eur_now and eur_30d:
                eur_chg = ((eur_now - eur_30d) / eur_30d) * 100
                metrics["eurusd"] = round(eur_now, 4)
                metrics["eurusd_30d_change_pct"] = round(eur_chg, 2)

        # ── S&P 500 (BTC correlation ρ=0.72-0.87) ───────────────
        if len(sp500) >= 22:
            sp_now = self.last_value(sp500)
            sp_30d = self.last_value(sp500, 21)
            if sp_now and sp_30d:
                sp_chg = ((sp_now - sp_30d) / sp_30d) * 100
                metrics["sp500"] = round(sp_now, 2)
                metrics["sp500_30d_return_pct"] = round(sp_chg, 2)

                if sp_chg < -5:
                    signals.append(("bearish", 0.7, f"S&P down {sp_chg:.1f}% — crypto correlated selling"))
                elif sp_chg > 5:
                    signals.append(("bullish", 0.5, f"S&P up {sp_chg:.1f}% — risk appetite strong"))

        # ── Synthesize ───────────────────────────────────────────
        if not signals:
            return AgentSignal(
                agent_name=self.name, regime="unknown", signal="neutral",
                confidence=0.3, summary="Insufficient dollar/vol data.",
                metrics=metrics,
            )

        bullish = sum(c for s, c, _ in signals if s == "bullish")
        bearish = sum(c for s, c, _ in signals if s in ("bearish", "caution"))
        total = sum(c for _, c, _ in signals)

        if bearish > bullish * 1.5:
            regime = "risk_off"
            signal = "bearish"
        elif bullish > bearish * 1.5:
            regime = "risk_on"
            signal = "bullish"
        else:
            regime = "mixed"
            signal = "caution"

        # VIX > 30 always overrides to bearish
        vix_val = metrics.get("vix", 20)
        if vix_val > 30:
            regime, signal = "panic", "bearish"

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
