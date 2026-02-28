"""
Liquidity Agent — Monitors global liquidity conditions that drive crypto.

M2 money supply has a 0.94 correlation with Bitcoin price (90-day lead).
Fed balance sheet expansion/contraction (QE/QT) directly drives risk appetite.
Reverse repo drain = capital seeking yield = flows into crypto/DeFi.
TGA drawdown = stealth liquidity injection.
"""

from agents.base_agent import BaseAgent, AgentSignal


class LiquidityAgent(BaseAgent):
    name = "liquidity"

    def analyze(self, data: dict[str, list[dict]]) -> AgentSignal:
        m2 = data.get("M2SL", [])
        fed_bs = data.get("WALCL", [])
        rrp = data.get("RRPONTSYD", [])
        tga = data.get("WTREGEN", [])

        metrics = {}
        signals = []

        # ── M2 Money Supply (monthly) ────────────────────────────
        if len(m2) >= 2:
            m2_current = self.last_value(m2)
            m2_prev = self.last_value(m2, 1)
            m2_yoy_prev = self.last_value(m2, 12) if len(m2) >= 13 else None

            if m2_current and m2_prev:
                m2_mom = ((m2_current - m2_prev) / m2_prev) * 100
                metrics["m2_level_billions"] = round(m2_current, 1)
                metrics["m2_mom_pct"] = round(m2_mom, 3)

                if m2_yoy_prev:
                    m2_yoy = ((m2_current - m2_yoy_prev) / m2_yoy_prev) * 100
                    metrics["m2_yoy_pct"] = round(m2_yoy, 2)
                    # M2 growing > 4% YoY = bullish crypto (90-day lead)
                    if m2_yoy > 4:
                        signals.append(("bullish", 0.8, "M2 expanding >4% YoY — bullish crypto w/ 90d lag"))
                    elif m2_yoy > 0:
                        signals.append(("neutral", 0.5, "M2 growing modestly"))
                    else:
                        signals.append(("bearish", 0.7, "M2 contracting — liquidity headwind"))

        # ── Fed Balance Sheet (weekly) ───────────────────────────
        if len(fed_bs) >= 5:
            bs_current = self.last_value(fed_bs)
            bs_4w_ago = self.last_value(fed_bs, 4) if len(fed_bs) >= 5 else None
            bs_12w_ago = self.last_value(fed_bs, 12) if len(fed_bs) >= 13 else None

            if bs_current:
                metrics["fed_bs_trillions"] = round(bs_current / 1e6, 3)
                if bs_4w_ago:
                    bs_4w_chg = bs_current - bs_4w_ago
                    metrics["fed_bs_4w_change_billions"] = round(bs_4w_chg / 1e3, 1)
                    if bs_4w_chg > 0:
                        signals.append(("bullish", 0.7, "Fed balance sheet expanding (QE/liquidity)"))
                    elif bs_4w_chg < -20000:  # >$20B decline in 4 weeks
                        signals.append(("bearish", 0.6, "Fed balance sheet shrinking (QT active)"))

        # ── Reverse Repo (daily) ─────────────────────────────────
        if len(rrp) >= 2:
            rrp_current = self.last_value(rrp)
            rrp_30d_ago = self.last_value(rrp, 22) if len(rrp) >= 23 else None
            rrp_90d_ago = self.last_value(rrp, 65) if len(rrp) >= 66 else None

            if rrp_current is not None:
                metrics["rrp_billions"] = round(rrp_current, 1)
                if rrp_30d_ago:
                    rrp_30d_chg = rrp_current - rrp_30d_ago
                    metrics["rrp_30d_change_billions"] = round(rrp_30d_chg, 1)
                    # RRP draining = liquidity entering system = bullish
                    if rrp_30d_chg < -50:
                        signals.append(("bullish", 0.6, "RRP draining — liquidity seeking yield"))
                    elif rrp_current < 100:
                        signals.append(("neutral", 0.5, "RRP nearly depleted — drain complete"))

        # ── Treasury General Account (weekly) ────────────────────
        if len(tga) >= 2:
            tga_current = self.last_value(tga)
            tga_4w_ago = self.last_value(tga, 4) if len(tga) >= 5 else None

            if tga_current:
                metrics["tga_billions"] = round(tga_current / 1e3, 1)
                if tga_4w_ago:
                    tga_chg = tga_current - tga_4w_ago
                    metrics["tga_4w_change_billions"] = round(tga_chg / 1e3, 1)
                    # TGA drawdown = Treasury spending = liquidity injection
                    if tga_chg < -50000:  # >$50B decline
                        signals.append(("bullish", 0.5, "TGA drawdown — stealth liquidity injection"))

        # ── Synthesize ───────────────────────────────────────────
        if not signals:
            return AgentSignal(
                agent_name=self.name, regime="unknown", signal="neutral",
                confidence=0.3, summary="Insufficient liquidity data.",
                metrics=metrics,
            )

        bullish = sum(c for s, c, _ in signals if s == "bullish")
        bearish = sum(c for s, c, _ in signals if s == "bearish")
        total = sum(c for _, c, _ in signals)

        if bullish > bearish * 1.5:
            regime, signal = "expanding", "bullish"
        elif bearish > bullish * 1.5:
            regime, signal = "tightening", "bearish"
        elif total > 0 and bullish / total > 0.6:
            regime, signal = "neutral_to_loose", "neutral"
        else:
            regime, signal = "mixed", "caution"

        conf = min(0.9, total / (len(signals) * 0.8))
        summaries = [s for _, _, s in signals]

        return AgentSignal(
            agent_name=self.name,
            regime=regime,
            signal=signal,
            confidence=round(conf, 2),
            summary=". ".join(summaries[:3]),
            details={"regime_label": regime.replace("_", " ").title()},
            metrics=metrics,
        )
