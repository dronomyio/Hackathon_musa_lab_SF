"""
Macro Economic Ontology — Neo4j Knowledge Graph
================================================

Seeds and queries a knowledge graph encoding:
  - FRED series → Agent → Domain → Vertical relationships
  - Causal transmission channels (M2 → BTC, VIX → MEV, etc.)
  - Threshold triggers (VIX>30 → liquidation cascades)
  - Cross-domain dependencies (credit widening → DeFi TVL outflows)
  - Regime classification rules

The orchestrator queries this graph before synthesis to:
  1. Understand WHY signals are connected (not just that they correlate)
  2. Trace causal paths: "yield curve inversion → recession signal → risk-off → crypto drawdown"
  3. Identify which transmission channels are active given current data
  4. Provide Opus 4.6 with structured causal context alongside raw FRED numbers

Usage:
    python -m core.ontology seed    # Build the graph
    python -m core.ontology query   # Test queries
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("ontology")

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "macroplatform2026")


def get_driver():
    """Get Neo4j driver."""
    from neo4j import GraphDatabase
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


# ═══════════════════════════════════════════════════════════════════
#  Ontology Schema — Node and Relationship Types
# ═══════════════════════════════════════════════════════════════════
#
#  Nodes:
#    (:FREDSeries {id, name, category, frequency, units})
#    (:Agent {id, name, description})
#    (:Domain {id, label, description})
#    (:Vertical {id, name, icon, color, is_primary})
#    (:Regime {id, label, description})
#    (:Indicator {id, name, type})  — derived metrics like spreads, ratios
#    (:Threshold {id, metric, operator, value, description})
#    (:TransmissionChannel {id, name, correlation, lag_days, description})
#
#  Relationships:
#    (Agent)-[:ANALYZES]->(FREDSeries)
#    (Agent)-[:BELONGS_TO]->(Domain)
#    (Domain)-[:SERVES]->(Vertical)
#    (FREDSeries)-[:FEEDS]->(Indicator)
#    (Indicator)-[:TRIGGERS {condition}]->(Regime)
#    (Regime)-[:ACTIVATES]->(TransmissionChannel)
#    (TransmissionChannel)-[:TRANSMITS_TO {correlation, lag}]->(Domain)
#    (Threshold)-[:MONITORS]->(Indicator)
#    (Threshold)-[:FIRES]->(Regime)
#    (Domain)-[:CAUSES {lag_days, strength}]->(Domain)
# ═══════════════════════════════════════════════════════════════════


def seed_ontology():
    """Build the complete macro economic ontology."""
    driver = get_driver()

    with driver.session() as session:
        # Clear existing
        session.run("MATCH (n) DETACH DELETE n")
        logger.info("Cleared existing graph")

        # ── Constraints & Indexes ──
        for label in ["FREDSeries", "Agent", "Domain", "Vertical", "Regime", "Indicator", "Threshold", "TransmissionChannel"]:
            try:
                session.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE")
            except Exception:
                pass

        # ── Agents ──
        agents = [
            ("yield_curve", "Yield Curve Agent", "Analyzes treasury yield curve shape, steepening/flattening, inversion signals"),
            ("credit", "Credit Risk Agent", "Monitors corporate spreads, HY vs IG, default risk indicators"),
            ("inflation", "Inflation Agent", "Tracks CPI/PCE trends, breakevens, inflation expectations anchoring"),
            ("tail_risk", "Tail Risk Agent", "Detects extreme spread percentiles, 30Y-10Y term premium anomalies"),
            ("cross_correlation", "Cross-Correlation Agent", "Measures synchronized movement across series, unified policy signals"),
            ("liquidity", "Liquidity Agent", "Tracks M2, Fed balance sheet, RRP depletion, financial conditions"),
            ("dollar_vol", "Dollar/Volatility Agent", "Monitors USD strength, VIX regime, risk-on/risk-off positioning"),
            ("employment_stress", "Employment/Stress Agent", "Analyzes jobless claims, NFCI, payrolls, labor market tightness"),
        ]
        for aid, name, desc in agents:
            session.run(
                "CREATE (:Agent {id: $id, name: $name, description: $desc})",
                id=aid, name=name, desc=desc,
            )

        # ── Domains ──
        domains = [
            ("yield_curve", "Yield Curve & Rates"),
            ("credit", "Credit Spreads & Corporate Debt"),
            ("inflation", "Inflation & Price Expectations"),
            ("fed_policy", "Fed Policy & Monetary"),
            ("liquidity", "Liquidity & Money Supply"),
            ("dollar_vol", "Dollar & Volatility"),
            ("employment", "Employment & Labor Market"),
            ("macro_crypto", "Macro → Crypto Transmission"),
            ("housing", "Housing & Real Estate"),
            ("fiscal", "Fiscal Policy & Government"),
            ("trade", "Trade & Supply Chain"),
        ]
        for did, label in domains:
            session.run("CREATE (:Domain {id: $id, label: $label})", id=did, label=label)

        # ── Verticals ──
        verticals = [
            ("defi_crypto", "DeFi & Crypto", "⚡", "#06b6d4", True),
            ("county_fiscal", "County GDP & Fiscal", "🏛️", "#8b5cf6", False),
            ("housing", "Housing & Real Estate", "🏠", "#f59e0b", False),
            ("small_business", "Small Business & Main Street", "🏪", "#22c55e", False),
            ("inflation_impact", "Inflation & Consumer Impact", "💰", "#ef4444", False),
            ("agriculture", "Agriculture & Commodities", "🌾", "#84cc16", False),
            ("trade_supply", "Trade & Supply Chain", "🚢", "#0ea5e9", False),
            ("labor_market", "Labor Market & Workforce", "👷", "#ec4899", False),
        ]
        for vid, name, icon, color, primary in verticals:
            session.run(
                "CREATE (:Vertical {id: $id, name: $name, icon: $icon, color: $color, is_primary: $primary})",
                id=vid, name=name, icon=icon, color=color, primary=primary,
            )

        # ── Agent → Domain mappings ──
        agent_domain = [
            ("yield_curve", "yield_curve"), ("credit", "credit"),
            ("inflation", "inflation"), ("tail_risk", "yield_curve"),
            ("cross_correlation", "fed_policy"), ("liquidity", "liquidity"),
            ("dollar_vol", "dollar_vol"), ("employment_stress", "employment"),
        ]
        for aid, did in agent_domain:
            session.run("""
                MATCH (a:Agent {id: $aid}), (d:Domain {id: $did})
                CREATE (a)-[:BELONGS_TO]->(d)
            """, aid=aid, did=did)

        # ── Domain → Vertical mappings ──
        domain_vertical = [
            ("yield_curve", "defi_crypto"), ("credit", "defi_crypto"),
            ("inflation", "defi_crypto"), ("liquidity", "defi_crypto"),
            ("dollar_vol", "defi_crypto"), ("employment", "defi_crypto"),
            ("fed_policy", "defi_crypto"), ("macro_crypto", "defi_crypto"),
            ("fiscal", "county_fiscal"), ("housing", "housing"),
            ("employment", "labor_market"), ("inflation", "inflation_impact"),
            ("trade", "trade_supply"),
        ]
        for did, vid in domain_vertical:
            session.run("""
                MATCH (d:Domain {id: $did}), (v:Vertical {id: $vid})
                CREATE (d)-[:SERVES]->(v)
            """, did=did, vid=vid)

        # ── Key FRED Series (core 49) ──
        core_series = [
            ("DGS2", "2-Year Treasury", "yield_curve"),
            ("DGS10", "10-Year Treasury", "yield_curve"),
            ("DGS30", "30-Year Treasury", "yield_curve"),
            ("T10Y2Y", "10Y-2Y Spread", "yield_curve"),
            ("T10Y3M", "10Y-3M Spread", "yield_curve"),
            ("BAA10Y", "Baa-10Y Credit Spread", "credit"),
            ("BAMLH0A0HYM2", "ICE BofA HY OAS", "credit"),
            ("CPIAUCSL", "CPI All Urban", "inflation"),
            ("PCEPI", "PCE Price Index", "inflation"),
            ("T10YIE", "10Y Breakeven Inflation", "inflation"),
            ("M2SL", "M2 Money Supply", "liquidity"),
            ("WALCL", "Fed Balance Sheet", "liquidity"),
            ("RRPONTSYD", "Overnight Reverse Repo", "liquidity"),
            ("NFCI", "Financial Conditions Index", "liquidity"),
            ("VIXCLS", "VIX", "dollar_vol"),
            ("DTWEXBGS", "USD Trade-Weighted Index", "dollar_vol"),
            ("SP500", "S&P 500", "dollar_vol"),
            ("UNRATE", "Unemployment Rate", "employment"),
            ("ICSA", "Initial Jobless Claims", "employment"),
            ("PAYEMS", "Nonfarm Payrolls", "employment"),
            ("FEDFUNDS", "Fed Funds Rate", "fed_policy"),
            ("STLFSI4", "St. Louis Financial Stress", "employment"),
        ]
        for sid, name, domain in core_series:
            session.run(
                "CREATE (:FREDSeries {id: $id, name: $name, category: $domain})",
                id=sid, name=name, domain=domain,
            )
            # Link to analyzing agent
            agent_map = {
                "yield_curve": "yield_curve", "credit": "credit",
                "inflation": "inflation", "liquidity": "liquidity",
                "dollar_vol": "dollar_vol", "employment": "employment_stress",
                "fed_policy": "cross_correlation",
            }
            agent_id = agent_map.get(domain)
            if agent_id:
                session.run("""
                    MATCH (a:Agent {id: $aid}), (s:FREDSeries {id: $sid})
                    CREATE (a)-[:ANALYZES]->(s)
                """, aid=agent_id, sid=sid)

        # ── Derived Indicators ──
        indicators = [
            ("yield_curve_slope", "Yield Curve Slope (10Y-2Y)", "spread"),
            ("real_rate", "Real Interest Rate (10Y - Breakeven)", "spread"),
            ("credit_stress", "Credit Stress (HY OAS)", "spread"),
            ("m2_yoy", "M2 Year-over-Year Growth", "growth_rate"),
            ("rrp_depletion", "RRP Depletion Rate", "flow"),
            ("vix_regime", "VIX Regime Level", "threshold"),
            ("usd_trend", "USD Trend Direction", "momentum"),
        ]
        for iid, name, itype in indicators:
            session.run(
                "CREATE (:Indicator {id: $id, name: $name, type: $type})",
                id=iid, name=name, type=itype,
            )

        # Series → Indicator feeds
        feeds = [
            ("T10Y2Y", "yield_curve_slope"), ("DGS10", "real_rate"),
            ("T10YIE", "real_rate"), ("BAMLH0A0HYM2", "credit_stress"),
            ("M2SL", "m2_yoy"), ("RRPONTSYD", "rrp_depletion"),
            ("VIXCLS", "vix_regime"), ("DTWEXBGS", "usd_trend"),
        ]
        for sid, iid in feeds:
            session.run("""
                MATCH (s:FREDSeries {id: $sid}), (i:Indicator {id: $iid})
                CREATE (s)-[:FEEDS]->(i)
            """, sid=sid, iid=iid)

        # ── Regimes ──
        regimes = [
            ("expansion", "Goldilocks Expansion", "Risk-on: yields stable, spreads tight, VIX low"),
            ("tightening", "Monetary Tightening", "Fed hiking, curve flattening, credit stress rising"),
            ("recession", "Recession Risk", "Curve inverted, claims rising, credit widening"),
            ("liquidity_boom", "Liquidity Expansion", "M2 growing, RRP depleting, financial conditions loose"),
            ("fiscal_stress", "Fiscal Dominance", "Long-end yields rising on supply, term premium expanding"),
            ("risk_off", "Risk-Off Panic", "VIX>30, flight to quality, liquidation cascades"),
            ("crypto_bull", "Crypto Bull Transmission", "M2 expanding, USD weakening, risk-on confirmed"),
            ("crypto_bear", "Crypto Bear Transmission", "Liquidity contracting, USD strengthening, credit stress"),
        ]
        for rid, label, desc in regimes:
            session.run(
                "CREATE (:Regime {id: $id, label: $label, description: $desc})",
                id=rid, label=label, desc=desc,
            )

        # ── Thresholds ──
        thresholds = [
            ("vix_panic", "vix_regime", ">", 30, "VIX > 30 triggers panic regime and MEV liquidation cascades"),
            ("vix_complacency", "vix_regime", "<", 14, "VIX < 14 signals complacency, potential volatility spike"),
            ("m2_bull", "m2_yoy", ">", 4.0, "M2 YoY > 4% activates primary crypto bull transmission"),
            ("m2_bear", "m2_yoy", "<", 2.0, "M2 YoY < 2% breaks crypto liquidity transmission"),
            ("curve_inversion", "yield_curve_slope", "<", 0, "Negative 10Y-2Y signals recession within 12-18 months"),
            ("credit_crisis", "credit_stress", ">", 500, "HY OAS > 500bp signals credit crisis, DeFi TVL outflows"),
            ("fiscal_alarm", "yield_curve_slope", ">", 75, "30Y-10Y > 75bp percentile signals fiscal tail risk"),
        ]
        for tid, indicator, operator, value, desc in thresholds:
            session.run(
                "CREATE (:Threshold {id: $id, metric: $indicator, operator: $op, value: $val, description: $desc})",
                id=tid, indicator=indicator, op=operator, val=value, desc=desc,
            )
            session.run("""
                MATCH (t:Threshold {id: $tid}), (i:Indicator {id: $iid})
                CREATE (t)-[:MONITORS]->(i)
            """, tid=tid, iid=indicator)

        # Thresholds fire regimes
        threshold_regime = [
            ("vix_panic", "risk_off"), ("m2_bull", "crypto_bull"),
            ("m2_bear", "crypto_bear"), ("curve_inversion", "recession"),
            ("credit_crisis", "recession"), ("fiscal_alarm", "fiscal_stress"),
        ]
        for tid, rid in threshold_regime:
            session.run("""
                MATCH (t:Threshold {id: $tid}), (r:Regime {id: $rid})
                CREATE (t)-[:FIRES]->(r)
            """, tid=tid, rid=rid)

        # ── Transmission Channels (the core IP) ──
        channels = [
            ("m2_btc", "M2 → BTC Liquidity", 0.94, 90,
             "M2 money supply expansion creates crypto demand via portfolio rebalancing and inflation hedging"),
            ("sp500_btc", "S&P 500 → BTC Equity Beta", 0.80, 2,
             "Equity risk-on confirms crypto positioning, 24-48hr lead time"),
            ("usd_btc", "USD → BTC Inverse", -0.50, 0,
             "Strong dollar = crypto headwind, weak dollar = tailwind. Real-time transmission"),
            ("vix_mev", "VIX → MEV Liquidation", 0.85, 0,
             "VIX > 30 triggers panic selling, cascading DeFi liquidations, MEV extraction spikes"),
            ("credit_defi", "Credit → DeFi TVL", 0.65, 3,
             "HY spread widening causes institutional DeFi withdrawal, TVL outflows within 24-72hrs"),
            ("ism_altseason", "ISM → Altseason", 0.55, 30,
             "ISM > 50 (expansion) triggers risk appetite rotation into altcoins within ~30 days"),
            ("rrp_stablecoin", "RRP → Stablecoin Supply", 0.70, 14,
             "RRP depletion releases reserves, some flow into stablecoin minting within 2 weeks"),
        ]
        for cid, name, corr, lag, desc in channels:
            session.run(
                "CREATE (:TransmissionChannel {id: $id, name: $name, correlation: $corr, lag_days: $lag, description: $desc})",
                id=cid, name=name, corr=corr, lag=lag, desc=desc,
            )

        # Regime → activates channels
        regime_channels = [
            ("crypto_bull", "m2_btc"), ("crypto_bull", "sp500_btc"),
            ("crypto_bull", "ism_altseason"), ("crypto_bull", "rrp_stablecoin"),
            ("crypto_bear", "usd_btc"), ("crypto_bear", "credit_defi"),
            ("risk_off", "vix_mev"), ("risk_off", "credit_defi"),
            ("liquidity_boom", "m2_btc"), ("liquidity_boom", "rrp_stablecoin"),
        ]
        for rid, cid in regime_channels:
            session.run("""
                MATCH (r:Regime {id: $rid}), (c:TransmissionChannel {id: $cid})
                CREATE (r)-[:ACTIVATES]->(c)
            """, rid=rid, cid=cid)

        # Channels transmit to domains
        channel_domains = [
            ("m2_btc", "macro_crypto"), ("sp500_btc", "macro_crypto"),
            ("usd_btc", "macro_crypto"), ("vix_mev", "macro_crypto"),
            ("credit_defi", "macro_crypto"), ("credit_defi", "credit"),
            ("ism_altseason", "macro_crypto"), ("rrp_stablecoin", "liquidity"),
        ]
        for cid, did in channel_domains:
            session.run("""
                MATCH (c:TransmissionChannel {id: $cid}), (d:Domain {id: $did})
                CREATE (c)-[:TRANSMITS_TO]->(d)
            """, cid=cid, did=did)

        # ── Cross-Domain Causal Links ──
        causal_links = [
            ("fed_policy", "yield_curve", 0, 0.95, "Rate decisions directly move the curve"),
            ("yield_curve", "credit", 7, 0.80, "Curve shape affects corporate borrowing costs"),
            ("credit", "macro_crypto", 3, 0.65, "Credit stress spills into DeFi within days"),
            ("liquidity", "macro_crypto", 90, 0.94, "M2 expansion is primary crypto driver"),
            ("inflation", "fed_policy", 30, 0.85, "Inflation prints drive Fed reaction function"),
            ("employment", "fed_policy", 7, 0.75, "Labor data influences rate path"),
            ("dollar_vol", "macro_crypto", 0, 0.50, "USD/VIX inversely correlated with crypto"),
            ("fiscal", "yield_curve", 14, 0.70, "Treasury supply affects long-end yields"),
            ("housing", "inflation", 90, 0.60, "Shelter CPI lags actual rents by ~12 months"),
            ("trade", "inflation", 30, 0.45, "Tariffs and supply chain feed into goods CPI"),
        ]
        for src, tgt, lag, strength, desc in causal_links:
            session.run("""
                MATCH (s:Domain {id: $src}), (t:Domain {id: $tgt})
                CREATE (s)-[:CAUSES {lag_days: $lag, strength: $strength, description: $desc}]->(t)
            """, src=src, tgt=tgt, lag=lag, strength=strength, desc=desc)

        logger.info("Ontology seeded successfully")

    driver.close()


# ═══════════════════════════════════════════════════════════════════
#  Query Functions — called by the orchestrator
# ═══════════════════════════════════════════════════════════════════

def get_active_transmission_channels(regime: str) -> list[dict]:
    """Given a detected regime, return which transmission channels are active."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (r:Regime {id: $regime})-[:ACTIVATES]->(c:TransmissionChannel)-[:TRANSMITS_TO]->(d:Domain)
            RETURN c.id AS channel, c.name AS name, c.correlation AS correlation,
                   c.lag_days AS lag, c.description AS description,
                   collect(d.label) AS target_domains
            ORDER BY abs(c.correlation) DESC
        """, regime=regime)
        channels = [dict(r) for r in result]
    driver.close()
    return channels


def get_causal_chain(from_domain: str, to_domain: str, max_hops: int = 4) -> list[dict]:
    """
    Find causal paths between two domains.
    
    Example: get_causal_chain("fed_policy", "macro_crypto")
    Returns: fed_policy → yield_curve → credit → macro_crypto
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH path = (s:Domain {id: $from})-[:CAUSES*1..""" + str(max_hops) + """]->(t:Domain {id: $to})
            WITH path, reduce(total_lag = 0, r IN relationships(path) | total_lag + r.lag_days) AS total_lag,
                 reduce(strength = 1.0, r IN relationships(path) | strength * r.strength) AS chain_strength
            RETURN [n IN nodes(path) | n.label] AS path_labels,
                   [n IN nodes(path) | n.id] AS path_ids,
                   [r IN relationships(path) | r.description] AS causal_descriptions,
                   total_lag, chain_strength
            ORDER BY chain_strength DESC
            LIMIT 5
        """, **{"from": from_domain, "to": to_domain})
        chains = [dict(r) for r in result]
    driver.close()
    return chains


def get_threshold_alerts(indicators: dict) -> list[dict]:
    """
    Given current indicator values, check which thresholds are firing.
    
    Args:
        indicators: {"vix_regime": 31, "m2_yoy": 4.29, "yield_curve_slope": 0.61, ...}
    
    Returns: list of fired thresholds with their regime implications
    """
    driver = get_driver()
    alerts = []
    with driver.session() as session:
        result = session.run("""
            MATCH (t:Threshold)-[:MONITORS]->(i:Indicator)
            OPTIONAL MATCH (t)-[:FIRES]->(r:Regime)
            RETURN t.id AS threshold_id, t.metric AS metric, t.operator AS operator,
                   t.value AS threshold_value, t.description AS description,
                   i.name AS indicator_name,
                   r.id AS regime_id, r.label AS regime_label
        """)
        for record in result:
            metric = record["metric"]
            if metric not in indicators:
                continue
            current_value = indicators[metric]
            op = record["operator"]
            threshold_val = record["threshold_value"]

            fired = False
            if op == ">" and current_value > threshold_val:
                fired = True
            elif op == "<" and current_value < threshold_val:
                fired = True
            elif op == ">=" and current_value >= threshold_val:
                fired = True

            if fired:
                alerts.append({
                    "threshold": record["threshold_id"],
                    "indicator": record["indicator_name"],
                    "current_value": current_value,
                    "threshold_value": threshold_val,
                    "operator": op,
                    "description": record["description"],
                    "fires_regime": record["regime_label"],
                    "regime_id": record["regime_id"],
                })
    driver.close()
    return alerts


def get_context_for_synthesis(regime: str, indicators: dict) -> str:
    """
    Build a structured context string for Opus 4.6 from the knowledge graph.
    
    Injected into the orchestrator prompt alongside FRED data and commentary.
    Gives Opus causal reasoning, not just correlation numbers.
    """
    lines = ["## Ontology Context (Knowledge Graph)\n"]

    # Active transmission channels
    channels = get_active_transmission_channels(regime)
    if channels:
        lines.append(f"**Active Transmission Channels for regime '{regime}':**")
        for ch in channels:
            lines.append(
                f"  - {ch['name']} (ρ={ch['correlation']}, lag={ch['lag']}d): "
                f"{ch['description']} → {', '.join(ch['target_domains'])}"
            )
        lines.append("")

    # Threshold alerts
    alerts = get_threshold_alerts(indicators)
    if alerts:
        lines.append("**Threshold Alerts (currently firing):**")
        for a in alerts:
            lines.append(
                f"  - {a['indicator']}: {a['current_value']} {a['operator']} {a['threshold_value']} "
                f"→ {a['fires_regime']}. {a['description']}"
            )
        lines.append("")

    # Causal chain to crypto (always relevant for primary vertical)
    for source in ["liquidity", "credit", "fed_policy"]:
        chains = get_causal_chain(source, "macro_crypto", max_hops=3)
        if chains:
            best = chains[0]
            lines.append(
                f"**Causal Path:** {' → '.join(best['path_labels'])} "
                f"(total lag: {best['total_lag']}d, chain strength: {best['chain_strength']:.2f})"
            )

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m core.ontology [seed|query]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "seed":
        seed_ontology()
        print("Ontology seeded successfully")

    elif cmd == "query":
        # Test queries
        print("\n=== Active Channels (crypto_bull) ===")
        for ch in get_active_transmission_channels("crypto_bull"):
            print(f"  {ch['name']}: ρ={ch['correlation']}, lag={ch['lag']}d")

        print("\n=== Causal Chain: liquidity → macro_crypto ===")
        for chain in get_causal_chain("liquidity", "macro_crypto"):
            print(f"  {' → '.join(chain['path_labels'])} (strength={chain['chain_strength']:.2f})")

        print("\n=== Threshold Alerts ===")
        test_indicators = {"vix_regime": 31, "m2_yoy": 4.29, "yield_curve_slope": 0.61}
        for alert in get_threshold_alerts(test_indicators):
            print(f"  {alert['indicator']}: {alert['current_value']} → {alert['fires_regime']}")

        print("\n=== Full Context for Synthesis ===")
        print(get_context_for_synthesis("liquidity_boom", test_indicators))
