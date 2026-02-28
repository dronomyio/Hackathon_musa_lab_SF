"""FRED series definitions for Treasury + Macro + Crypto-relevant analysis."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SeriesDef:
    series_id: str
    name: str
    category: str
    maturity_years: Optional[float] = None
    frequency: str = "Daily"
    units: str = "Percent"


# ═══════════════════════════════════════════════════════════════════
#  TIER 1 — YIELD CURVE & SPREADS (existing)
# ═══════════════════════════════════════════════════════════════════

YIELD_CURVE_SERIES = [
    SeriesDef("DGS1MO", "1-Month Treasury", "yield_curve", 1 / 12),
    SeriesDef("DGS3MO", "3-Month Treasury", "yield_curve", 0.25),
    SeriesDef("DGS6MO", "6-Month Treasury", "yield_curve", 0.5),
    SeriesDef("DGS1", "1-Year Treasury", "yield_curve", 1),
    SeriesDef("DGS2", "2-Year Treasury", "yield_curve", 2),
    SeriesDef("DGS3", "3-Year Treasury", "yield_curve", 3),
    SeriesDef("DGS5", "5-Year Treasury", "yield_curve", 5),
    SeriesDef("DGS7", "7-Year Treasury", "yield_curve", 7),
    SeriesDef("DGS10", "10-Year Treasury", "yield_curve", 10),
    SeriesDef("DGS20", "20-Year Treasury", "yield_curve", 20),
    SeriesDef("DGS30", "30-Year Treasury", "yield_curve", 30),
]

SPREAD_SERIES = [
    SeriesDef("T10Y2Y", "10Y-2Y Spread", "spread"),
    SeriesDef("T10Y3M", "10Y-3M Spread", "spread"),
    SeriesDef("T10YFF", "10Y-FedFunds Spread", "spread"),
]

# ═══════════════════════════════════════════════════════════════════
#  TIER 2 — CORPORATE CREDIT (existing)
# ═══════════════════════════════════════════════════════════════════

CREDIT_SERIES = [
    SeriesDef("AAA", "Moody's Aaa Corporate Yield", "credit"),
    SeriesDef("BAA", "Moody's Baa Corporate Yield", "credit"),
    SeriesDef("BAA10Y", "Baa-10Y Credit Spread", "credit"),
    SeriesDef("BAMLH0A0HYM2", "ICE BofA HY OAS", "credit"),
    SeriesDef("BAMLC0A0CM", "ICE BofA IG OAS", "credit"),
]

# ═══════════════════════════════════════════════════════════════════
#  TIER 3 — INFLATION (existing + CPI/PCE/PPI)
# ═══════════════════════════════════════════════════════════════════

INFLATION_SERIES = [
    SeriesDef("DFII5", "5Y TIPS Real Yield", "inflation", 5),
    SeriesDef("DFII10", "10Y TIPS Real Yield", "inflation", 10),
    SeriesDef("DFII30", "30Y TIPS Real Yield", "inflation", 30),
    SeriesDef("T5YIE", "5Y Breakeven Inflation", "inflation"),
    SeriesDef("T10YIE", "10Y Breakeven Inflation", "inflation"),
    SeriesDef("T5YIFR", "5Y5Y Forward Inflation", "inflation"),
    # Hard inflation data (monthly — FRED returns latest)
    SeriesDef("CPIAUCSL", "CPI Urban Consumers", "inflation_hard", frequency="Monthly", units="Index"),
    SeriesDef("PCEPI", "PCE Price Index (Fed preferred)", "inflation_hard", frequency="Monthly", units="Index"),
    SeriesDef("PPIFIS", "PPI Final Demand", "inflation_hard", frequency="Monthly", units="Index"),
    SeriesDef("CPILFESL", "Core CPI (ex Food & Energy)", "inflation_hard", frequency="Monthly", units="Index"),
]

# ═══════════════════════════════════════════════════════════════════
#  TIER 4 — FED POLICY (existing)
# ═══════════════════════════════════════════════════════════════════

FED_POLICY_SERIES = [
    SeriesDef("FEDFUNDS", "Fed Funds Effective Rate", "fed_policy"),
    SeriesDef("DFEDTARU", "Fed Funds Target Upper", "fed_policy"),
    SeriesDef("DFEDTARL", "Fed Funds Target Lower", "fed_policy"),
]

# ═══════════════════════════════════════════════════════════════════
#  TIER 5 — LIQUIDITY (NEW — highest crypto correlation)
# ═══════════════════════════════════════════════════════════════════

LIQUIDITY_SERIES = [
    # M2 money supply — 0.94 correlation with BTC, 90-day lead
    SeriesDef("M2SL", "M2 Money Supply", "liquidity", frequency="Monthly", units="Billions USD"),
    # Fed balance sheet — QT/QE proxy, direct risk appetite driver
    SeriesDef("WALCL", "Fed Total Assets (Balance Sheet)", "liquidity", frequency="Weekly", units="Millions USD"),
    # Reverse repo — liquidity drain; when it drops, capital seeks yield → crypto
    SeriesDef("RRPONTSYD", "ON RRP Facility Balance", "liquidity", frequency="Daily", units="Billions USD"),
    # Treasury General Account — drawdown = stealth liquidity injection
    SeriesDef("WTREGEN", "Treasury General Account", "liquidity", frequency="Weekly", units="Millions USD"),
]

# ═══════════════════════════════════════════════════════════════════
#  TIER 6 — DOLLAR & GLOBAL RISK (NEW)
# ═══════════════════════════════════════════════════════════════════

DOLLAR_RISK_SERIES = [
    # Trade-weighted USD — inverse correlation to crypto
    SeriesDef("DTWEXBGS", "Trade-Weighted USD Index (Broad)", "dollar", frequency="Daily", units="Index"),
    # VIX — fear gauge, spikes → MEV liquidation cascades
    SeriesDef("VIXCLS", "CBOE VIX", "dollar", frequency="Daily", units="Index"),
    # TED spread — interbank stress → contagion risk
    SeriesDef("TEDRATE", "TED Spread", "dollar", frequency="Daily", units="Percent"),
    # EUR/USD — global risk sentiment
    SeriesDef("DEXUSEU", "USD/EUR Exchange Rate", "dollar", frequency="Daily", units="USD per EUR"),
]

# ═══════════════════════════════════════════════════════════════════
#  TIER 7 — EMPLOYMENT & GROWTH (NEW — leads Fed by 30-60 days)
# ═══════════════════════════════════════════════════════════════════

EMPLOYMENT_SERIES = [
    # Unemployment rate — rising → rate cuts → bullish crypto
    SeriesDef("UNRATE", "Unemployment Rate", "employment", frequency="Monthly", units="Percent"),
    # Non-farm payrolls — weak = dovish pivot
    SeriesDef("PAYEMS", "Non-Farm Payrolls", "employment", frequency="Monthly", units="Thousands"),
    # Initial jobless claims — WEEKLY, most timely recession signal
    SeriesDef("ICSA", "Initial Jobless Claims", "employment", frequency="Weekly", units="Number"),
    # Continued claims — labor market depth
    SeriesDef("CCSA", "Continued Jobless Claims", "employment", frequency="Weekly", units="Number"),
    # ISM Manufacturing PMI — above 50 = expansion = altseason trigger
    SeriesDef("MANEMP", "Manufacturing Employment", "employment", frequency="Monthly", units="Thousands"),
]

# ═══════════════════════════════════════════════════════════════════
#  TIER 8 — FINANCIAL STRESS (NEW — composite risk signals)
# ═══════════════════════════════════════════════════════════════════

STRESS_SERIES = [
    # St Louis Financial Stress Index — composite stress signal
    SeriesDef("STLFSI4", "StL Fed Financial Stress Index", "stress", frequency="Weekly", units="Index"),
    # Chicago NFCI — national financial conditions
    SeriesDef("NFCI", "Chicago Fed NFCI", "stress", frequency="Weekly", units="Index"),
    # Equity index for correlation
    SeriesDef("SP500", "S&P 500", "equity", frequency="Daily", units="Index"),
    SeriesDef("NASDAQCOM", "NASDAQ Composite", "equity", frequency="Daily", units="Index"),
]


# ═══════════════════════════════════════════════════════════════════
#  AGGREGATED LISTS
# ═══════════════════════════════════════════════════════════════════

ALL_SERIES = (
    YIELD_CURVE_SERIES
    + SPREAD_SERIES
    + CREDIT_SERIES
    + INFLATION_SERIES
    + FED_POLICY_SERIES
    + LIQUIDITY_SERIES
    + DOLLAR_RISK_SERIES
    + EMPLOYMENT_SERIES
    + STRESS_SERIES
)

# Core series (always fetched — yield curve + key indicators)
CORE_SERIES_IDS = (
    [s.series_id for s in YIELD_CURVE_SERIES + SPREAD_SERIES[:1]]
    + ["VIXCLS", "DTWEXBGS", "SP500"]
)

# Extended series (full agent suite)
EXTENDED_SERIES_IDS = [s.series_id for s in ALL_SERIES]

# Maturity labels for curve charts
MATURITY_LABELS = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
MATURITY_SERIES = [s.series_id for s in YIELD_CURVE_SERIES]

# Category groupings for the frontend
CATEGORY_GROUPS = {
    "yield_curve": [s.series_id for s in YIELD_CURVE_SERIES],
    "spread": [s.series_id for s in SPREAD_SERIES],
    "credit": [s.series_id for s in CREDIT_SERIES],
    "inflation": [s.series_id for s in INFLATION_SERIES],
    "fed_policy": [s.series_id for s in FED_POLICY_SERIES],
    "liquidity": [s.series_id for s in LIQUIDITY_SERIES],
    "dollar_risk": [s.series_id for s in DOLLAR_RISK_SERIES],
    "employment": [s.series_id for s in EMPLOYMENT_SERIES],
    "stress": [s.series_id for s in STRESS_SERIES],
}

SERIES_LOOKUP = {s.series_id: s for s in ALL_SERIES}
