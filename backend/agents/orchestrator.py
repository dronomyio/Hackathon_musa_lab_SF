"""
Orchestrator Agent — Claude Opus 4.6 as the synthesis engine.

8 specialist agents → Opus 4.6 orchestration → unified regime + DeFi/MEV signal.

PROMPT LIFECYCLE:
  1. Check prompt library for a curated/evolving/draft prompt
  2. If none exists → Opus 4.6 bootstraps one (meta-prompt generates domain-specific prompt)
  3. Every run → log performance metrics against the active prompt
  4. Draft auto-promotes to "evolving" after 20 good runs
  5. Human reviews via /api/prompts/* endpoints → "curated" = locked-in, battle-tested
  6. Self-improvement: Opus 4.6 can suggest prompt edits based on recurring blind spots
"""

import json
import logging
from datetime import datetime
from typing import Optional

import httpx

from core.config import get_settings
from core.prompt_lifecycle import (
    get_best_prompt, get_prompt, save_draft, log_run, curate_prompt,
)
from agents.base_agent import AgentSignal
from agents.yield_curve import YieldCurveAgent
from agents.credit_risk import CreditRiskAgent
from agents.inflation import InflationAgent
from agents.tail_risk import TailRiskAgent
from agents.cross_correlation import CrossCorrelationAgent
from agents.liquidity import LiquidityAgent
from agents.dollar_vol import DollarVolAgent
from agents.employment_stress import EmploymentStressAgent


log = logging.getLogger("orchestrator")

# The domains this 8-agent system covers
ACTIVE_DOMAINS = [
    "yield_curve", "credit_risk", "inflation", "tail_risk",
    "cross_correlation", "liquidity", "dollar_vol", "employment_stress",
]


# ═══════════════════════════════════════════════════════════════════════════════
#  BOOTSTRAP META-PROMPT
#
#  When no curated prompt exists, Opus 4.6 generates the orchestrator system
#  prompt itself. This meta-prompt tells it HOW to write a good system prompt.
#  It's the only hardcoded prompt — everything else is generated and curated.
# ═══════════════════════════════════════════════════════════════════════════════

BOOTSTRAP_META_PROMPT = """You are a prompt engineer specializing in macro-financial analysis systems.
Your job: write a SYSTEM PROMPT for an AI macro strategist that synthesizes bond market and
macro indicator signals into DeFi/crypto regime assessments.

The system has these agents producing structured data:
{agent_descriptions}

REQUIREMENTS for the system prompt you write:
1. Define the AI's role: "chief macro strategist bridging TradFi and DeFi"
2. Describe each agent and what it monitors
3. Include SPECIFIC macro→crypto transmission channels with correlation values:
   - M2 → BTC: ρ=0.94, 90-day lead
   - S&P → BTC: ρ=0.72-0.87 (2024-2025)
   - USD → BTC: ρ≈-0.5 (inverse)
   - Fed policy drives ~60% of crypto volatility
   - Credit → DeFi contagion: 24-72h lag
   - VIX > 30 = panic = MEV liquidation cascades
   - ISM > 50 = altseason trigger
   - Jobless claims > 300K = recession territory
   - STLFSI > 1.0 = systemic risk → crypto contagion
4. Specify the JSON output schema with ALL these fields:
   market_regime, regime_label, dominant_signal, confidence, headline, narrative,
   key_risks, regime_triggers, agent_agreement, conflicts, signal_weights,
   defi_implications (risk_appetite, tvl_outlook, stablecoin_pressure, mev_activity,
   liquidation_risk, btc_bias, altseason_probability, defi_yield_vs_tbill, narrative),
   macro_crypto_transmission (primary_channel, transmission_lag_days, signal_strength, description)
5. Emphasize: interactions between signals, conflicts, time-sequencing, specific numbers

Write ONLY the system prompt text. No preamble, no explanation. Start with "You are..."."""

AGENT_DESCRIPTIONS = """1. Yield Curve Agent — curve shape, 10Y-2Y spread, recession probability, transition detection
2. Credit Risk Agent — Aaa/Baa spreads, HY OAS, IG OAS, credit regime
3. Inflation Agent — 5Y/10Y breakevens, 5Y5Y forward, TIPS real yields, CPI/PCE trend
4. Tail Risk Agent — 20Y/30Y long-duration, term premium, fiscal risk
5. Cross-Correlation Agent — rolling 2Y-10Y yield change correlation, regime divergence
6. Liquidity Agent — M2 money supply, Fed balance sheet, reverse repo, TGA
7. Dollar & Volatility Agent — USD index, VIX, TED spread, S&P 500, EUR/USD
8. Employment & Stress Agent — jobless claims, unemployment, NFCI, financial stress"""


# ═══════════════════════════════════════════════════════════════════════════════
#  SELF-IMPROVEMENT META-PROMPT
#
#  After N runs, Opus 4.6 reviews the current prompt's performance and suggests
#  edits. These suggestions go into the prompt library as "proposed_edits" for
#  human review — the AI never self-modifies a curated prompt.
# ═══════════════════════════════════════════════════════════════════════════════

SELF_IMPROVE_META_PROMPT = """You are reviewing the performance of a macro analysis system prompt.

CURRENT SYSTEM PROMPT:
{current_prompt}

PERFORMANCE DATA (last {run_count} runs):
- Average confidence: {avg_confidence:.2f}
- Regime changes detected: {regime_changes}
- Agent conflicts detected: {conflicts_detected}
- Common blind spots or recurring issues: {blind_spots}

RECENT SYNTHESIS SAMPLES (last 3 runs):
{recent_samples}

TASK: Suggest specific improvements to the system prompt.
Focus on:
1. Are there macro→crypto transmission channels missing?
2. Are threshold values outdated? (e.g., "VIX > 30" might need updating)
3. Are there recurring conflicts the prompt doesn't handle well?
4. Is the confidence calibration good? (high confidence = actually correct?)
5. Are DeFi implications specific enough?

Respond with:
{{
  "improvements": [
    {{
      "section": "which part of the prompt to edit",
      "current": "current text (brief)",
      "suggested": "new text",
      "reasoning": "why this change"
    }}
  ],
  "overall_assessment": "1-2 sentences on prompt health",
  "urgency": "low | medium | high"
}}"""


class OrchestratorAgent:
    """8-agent orchestrator with prompt lifecycle management."""

    def __init__(self, correlation_window: int = 30):
        self.yield_curve_agent = YieldCurveAgent()
        self.credit_risk_agent = CreditRiskAgent()
        self.inflation_agent = InflationAgent()
        self.tail_risk_agent = TailRiskAgent()
        self.cross_corr_agent = CrossCorrelationAgent()
        self.liquidity_agent = LiquidityAgent()
        self.dollar_vol_agent = DollarVolAgent()
        self.employment_stress_agent = EmploymentStressAgent()
        self.correlation_window = correlation_window
        self._recent_syntheses: list[dict] = []  # Keep last 5 for self-improvement

    async def run_all(self, data: dict[str, list[dict]]) -> dict:
        """Execute all 8 agents, then synthesize via Claude or fallback."""
        signals = {}
        signals["yield_curve"] = self.yield_curve_agent.analyze(data)
        signals["credit_risk"] = self.credit_risk_agent.analyze(data)
        signals["inflation"] = self.inflation_agent.analyze(data)
        signals["tail_risk"] = self.tail_risk_agent.analyze(data)
        signals["cross_correlation"] = self.cross_corr_agent.analyze(
            data, window=self.correlation_window
        )
        signals["liquidity"] = self.liquidity_agent.analyze(data)
        signals["dollar_vol"] = self.dollar_vol_agent.analyze(data)
        signals["employment_stress"] = self.employment_stress_agent.analyze(data)

        signals_dict = {k: v.to_dict() for k, v in signals.items()}

        settings = get_settings()
        if settings.has_anthropic:
            # Get or create system prompt via lifecycle
            system_prompt, prompt_status = await self._resolve_system_prompt()
            synthesis = await self._claude_synthesize(signals_dict, system_prompt)
            engine = "claude-opus-4.6"

            # Log performance for prompt evolution
            confidence = synthesis.get("confidence", 0.0)
            # Normalize: Opus may return 0-100 or 0-1
            if confidence > 1.0:
                confidence = confidence / 100.0
            regime = synthesis.get("market_regime", "unknown")
            conflicts = synthesis.get("conflicts", [])
            log_run(ACTIVE_DOMAINS, confidence, regime, conflicts)

            # Track for self-improvement
            self._recent_syntheses.append({
                "timestamp": datetime.now().isoformat(),
                "regime": regime,
                "confidence": confidence,
                "conflicts": conflicts,
                "headline": synthesis.get("headline", ""),
            })
            self._recent_syntheses = self._recent_syntheses[-5:]

            # Add prompt metadata to response
            synthesis["_prompt_status"] = prompt_status
            synthesis["_prompt_version"] = (get_prompt(ACTIVE_DOMAINS) or {}).get("version", 0)
        else:
            synthesis = self._fallback_synthesize(signals)
            engine = "rule-based"
            prompt_status = "n/a"

        return {
            "signals": signals_dict,
            "synthesis": synthesis,
            "synthesis_engine": engine,
            "prompt_status": prompt_status,
            "agent_count": 8,
            "timestamp": datetime.now().isoformat(),
        }

    async def _resolve_system_prompt(self) -> tuple[str, str]:
        """
        Resolve the system prompt via lifecycle:
          1. Check for curated/evolving/draft prompt → use it
          2. If nothing → bootstrap a new one with meta-prompt → save as draft
        Returns (prompt_text, status).
        """
        existing = get_best_prompt(ACTIVE_DOMAINS)
        if existing:
            entry = get_prompt(ACTIVE_DOMAINS)
            status = entry["status"] if entry else "draft"
            log.info(f"Using {status} prompt v{entry.get('version', '?')}")
            return existing, status

        # No prompt exists — bootstrap one
        log.info("No prompt found. Bootstrapping via meta-prompt...")
        bootstrapped = await self._bootstrap_prompt()
        if bootstrapped:
            entry = save_draft(
                domains=ACTIVE_DOMAINS,
                system_prompt=bootstrapped,
                user_intent="8-agent treasury bond analysis with macro→DeFi transmission",
                generated_by="bootstrap-meta-prompt",
            )
            log.info(f"Saved bootstrapped prompt as draft v{entry['version']}")
            return bootstrapped, "draft"

        # Bootstrap failed — use hardcoded fallback
        log.warning("Bootstrap failed. Using hardcoded fallback prompt.")
        return self._hardcoded_fallback_prompt(), "fallback"

    async def _bootstrap_prompt(self) -> Optional[str]:
        """Use Opus 4.6 to generate the initial system prompt."""
        settings = get_settings()
        if not settings.has_anthropic:
            return None

        meta = BOOTSTRAP_META_PROMPT.format(agent_descriptions=AGENT_DESCRIPTIONS)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": settings.claude_model,
                        "max_tokens": 4000,
                        "messages": [{"role": "user", "content": meta}],
                    },
                    timeout=90.0,
                )
                resp.raise_for_status()
                data = resp.json()
                text = "".join(
                    b["text"] for b in data.get("content", []) if b.get("type") == "text"
                )
                return text.strip()
        except Exception as e:
            log.error(f"Bootstrap failed: {e}")
            return None

    async def suggest_improvements(self) -> Optional[dict]:
        """
        Ask Opus 4.6 to review the current prompt's performance and suggest edits.
        Called periodically (e.g. every 50 runs) or manually via API.
        Returns improvement suggestions for human review.
        """
        entry = get_prompt(ACTIVE_DOMAINS)
        if not entry or not entry.get("performance"):
            return None

        perf = entry["performance"]
        if perf.get("runs", 0) < 10:
            return {"message": "Not enough runs yet for self-improvement analysis"}

        settings = get_settings()
        if not settings.has_anthropic:
            return None

        # Format recent samples
        samples_text = json.dumps(self._recent_syntheses[-3:], indent=2, default=str)

        # Detect blind spots from performance data
        blind_spots = []
        if perf.get("avg_confidence", 0) < 0.5:
            blind_spots.append("Low average confidence — prompt may be too conservative or vague")
        if perf.get("conflicts_detected", 0) > perf.get("runs", 1) * 0.5:
            blind_spots.append("High conflict rate — agents frequently disagree, prompt may not handle conflicts well")
        if perf.get("regime_changes", 0) > perf.get("runs", 1) * 0.3:
            blind_spots.append("Frequent regime changes — possible noise or oversensitivity")

        meta = SELF_IMPROVE_META_PROMPT.format(
            current_prompt=entry["system_prompt"][:3000],  # Truncate for token budget
            run_count=perf["runs"],
            avg_confidence=perf.get("avg_confidence", 0),
            regime_changes=perf.get("regime_changes", 0),
            conflicts_detected=perf.get("conflicts_detected", 0),
            blind_spots="; ".join(blind_spots) if blind_spots else "None detected",
            recent_samples=samples_text,
        )

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": settings.claude_model,
                        "max_tokens": 2000,
                        "messages": [{"role": "user", "content": meta}],
                    },
                    timeout=60.0,
                )
                resp.raise_for_status()
                data = resp.json()
                text = "".join(
                    b["text"] for b in data.get("content", []) if b.get("type") == "text"
                ).strip()

                # Parse JSON response
                if "```" in text:
                    for part in text.split("```"):
                        clean = part.strip()
                        if clean.startswith("json"):
                            clean = clean[4:].strip()
                        try:
                            return json.loads(clean)
                        except json.JSONDecodeError:
                            continue
                return json.loads(text)
        except Exception as e:
            log.error(f"Self-improvement analysis failed: {e}")
            return {"error": str(e)}

    async def _claude_synthesize(self, signals_dict: dict, system_prompt: str) -> dict:
        """Synthesize using the resolved system prompt (curated or generated)."""
        settings = get_settings()

        clean_signals = {}
        for k, v in signals_dict.items():
            s = dict(v)
            if "details" in s and isinstance(s["details"], dict):
                d = dict(s["details"])
                d.pop("correlation_series", None)
                d.pop("correlation_dates", None)
                s["details"] = d
            clean_signals[k] = s

        user_prompt = f"""Current date: {datetime.now().strftime('%Y-%m-%d')}

## 8 Agent Outputs

{json.dumps(clean_signals, indent=2, default=str)}

Synthesize these into your unified market assessment. Respond ONLY with valid JSON, no markdown fences."""

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": settings.claude_model,
                        "max_tokens": 3000,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": user_prompt}],
                    },
                    timeout=60.0,
                )
                resp.raise_for_status()
                data = resp.json()

                text = ""
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        text += block["text"]

                text = text.strip()
                if "```" in text:
                    parts = text.split("```")
                    for part in parts:
                        clean = part.strip()
                        if clean.startswith("json"):
                            clean = clean[4:].strip()
                        try:
                            return json.loads(clean)
                        except json.JSONDecodeError:
                            continue

                return json.loads(text)

        except json.JSONDecodeError:
            return {
                "market_regime": "unknown",
                "regime_label": "Analysis Available (non-JSON)",
                "dominant_signal": "neutral",
                "confidence": 0.5,
                "headline": "Claude analysis completed",
                "narrative": text if "text" in dir() else "Parse error",
                "key_risks": [], "regime_triggers": [],
                "agent_agreement": False, "conflicts": [],
                "signal_weights": {},
                "defi_implications": {"narrative": "See main narrative."},
                "macro_crypto_transmission": {},
            }
        except httpx.HTTPStatusError as e:
            return self._error_fallback(f"Anthropic API {e.response.status_code}")
        except Exception as e:
            return self._error_fallback(str(e))

    def _hardcoded_fallback_prompt(self) -> str:
        """Last resort — if bootstrap fails and nothing in library."""
        return (
            "You are the chief macro strategist for a quantitative fund bridging TradFi and DeFi. "
            "You receive outputs from 8 agents: yield curve, credit risk, inflation, tail risk, "
            "cross-correlation, liquidity, dollar/volatility, employment/stress. "
            "Synthesize into a unified market regime assessment with DeFi implications. "
            "Key relationships: M2→BTC ρ=0.94 90d lag, USD→BTC ρ≈-0.5 inverse, VIX>30=liquidation cascades. "
            "Respond in JSON with: market_regime, regime_label, dominant_signal, confidence, headline, "
            "narrative, key_risks, regime_triggers, agent_agreement, conflicts, signal_weights, "
            "defi_implications, macro_crypto_transmission."
        )

    def _fallback_synthesize(self, signals: dict[str, AgentSignal]) -> dict:
        yc = signals["yield_curve"]
        cr = signals["credit_risk"]
        inf = signals["inflation"]
        liq = signals["liquidity"]
        dv = signals["dollar_vol"]
        es = signals["employment_stress"]

        spread = yc.metrics.get("spread_10y2y", 0)
        vix = dv.metrics.get("vix", 20)
        m2_yoy = liq.metrics.get("m2_yoy_pct", 0)

        # Regime detection with new signals
        if vix > 30 and cr.signal == "bearish":
            regime, label = "dislocation", "Market Dislocation"
        elif m2_yoy > 4 and dv.signal == "bullish":
            regime, label = "liquidity_driven_rally", "Liquidity-Driven Rally"
        elif inf.regime in ("unanchored_high",) and spread < 0.2:
            regime, label = "stagflation_risk", "Stagflation Risk"
        elif yc.regime == "inverted" or yc.metrics.get("recession_probability", 0) > 0.5:
            regime, label = ("recession_risk", "Recession Risk") if cr.signal == "bearish" else ("late_cycle_tightening", "Late-Cycle Tightening")
        elif spread > 0.5 and cr.signal != "bearish":
            regime, label = "risk_on_expansion", "Risk-On Expansion"
        else:
            regime, label = "transition", "Regime Transition"

        # 8-agent vote
        weights = {
            "yield_curve": 0.20, "credit_risk": 0.15, "inflation": 0.12,
            "tail_risk": 0.06, "cross_correlation": 0.07,
            "liquidity": 0.18, "dollar_vol": 0.12, "employment_stress": 0.10,
        }
        votes = {"bullish": 0, "bearish": 0, "caution": 0, "neutral": 0}
        for s in signals.values():
            votes[s.signal] = votes.get(s.signal, 0) + s.confidence
        dominant = max(votes, key=votes.get)
        conf = sum(signals[k].confidence * w for k, w in weights.items())

        risk = "high" if spread > 0.3 and cr.signal != "bearish" else (
            "low" if vix > 25 or cr.signal == "bearish" else "moderate"
        )

        return {
            "market_regime": regime,
            "regime_label": label,
            "dominant_signal": dominant,
            "confidence": round(conf, 2),
            "headline": f"{label} — 10Y-2Y: {spread:.2f}%, VIX: {vix:.0f}, M2 YoY: {m2_yoy:.1f}%",
            "narrative": (
                f"Rule-based synthesis (8 agents, no ANTHROPIC_API_KEY). "
                f"YC: {yc.regime}. Credit: {cr.regime}. Inflation: {inf.regime}. "
                f"Liquidity: {liq.regime}. Dollar/Vol: {dv.regime}. "
                f"Employment: {es.regime}. Add ANTHROPIC_API_KEY for Opus 4.6 analysis."
            ),
            "key_risks": [], "regime_triggers": [],
            "agent_agreement": len(set(s.signal for s in signals.values())) == 1,
            "conflicts": [],
            "signal_weights": weights,
            "defi_implications": {
                "risk_appetite": risk,
                "tvl_outlook": "contracting" if dominant == "bearish" else "stable",
                "stablecoin_pressure": "high" if spread < 0.1 else "low",
                "mev_activity": "elevated" if vix > 22 else "normal",
                "liquidation_risk": "high" if vix > 30 and cr.signal == "bearish" else "low",
                "btc_bias": "bearish" if dominant == "bearish" else "neutral",
                "altseason_probability": "low",
                "defi_yield_vs_tbill": "tbill_attractive" if spread > 0.3 else "neutral",
                "narrative": f"Rule-based. VIX={vix:.0f}, M2 YoY={m2_yoy:.1f}%. Add ANTHROPIC_API_KEY for rich analysis.",
            },
            "macro_crypto_transmission": {
                "primary_channel": "liquidity" if abs(m2_yoy) > 3 else "dollar",
                "transmission_lag_days": 90 if abs(m2_yoy) > 3 else 30,
                "signal_strength": "strong" if abs(m2_yoy) > 4 else "moderate",
                "description": "Rule-based transmission estimate.",
            },
        }

    def _error_fallback(self, error: str) -> dict:
        return {
            "market_regime": "unknown",
            "regime_label": "API Error — Fallback Mode",
            "dominant_signal": "neutral", "confidence": 0.0,
            "headline": f"Synthesis error: {error}",
            "narrative": "Claude API call failed. Displaying raw agent signals only.",
            "key_risks": [], "regime_triggers": [],
            "agent_agreement": False, "conflicts": [],
            "signal_weights": {},
            "defi_implications": {"narrative": "Unavailable."},
            "macro_crypto_transmission": {},
            "_error": error,
        }
