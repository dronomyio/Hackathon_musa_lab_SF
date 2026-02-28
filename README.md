# Macro Intelligence Platform — Project Writeup

Multi-vertical macro intelligence platform with 8 AI agents analyzing 127 FRED series across 8 verticals, powered by Claude Opus 4.6 synthesis and a Neo4j causal ontology.

## The Problem

Economic data is public, but economic understanding is not. The Federal Reserve publishes 800K+ time series covering yields, inflation, employment, housing, and trade — yet interpreting how these signals connect and cascade requires expertise concentrated in Wall Street institutions. A county treasurer managing bonds, a small business owner deciding whether to expand, a farmer hedging commodity exposure — all face the same complex macro environment but lack the analytical infrastructure to navigate it.

## What We Built

An AI-powered platform where 8 specialist agents continuously analyze 127 live FRED series and Claude Opus 4.6 synthesizes actionable intelligence across 8 verticals: DeFi/Crypto, County Fiscal, Housing, Small Business, Inflation Impact, Agriculture, Trade, and Labor Markets. A Neo4j knowledge graph encodes the causal ontology — not just that M2 correlates with BTC (ρ=0.94), but the transmission mechanism: Fed policy → yield curve → credit spreads → DeFi outflows, with measured lags and threshold triggers. When VIX crosses 30, the ontology fires a regime alert and traces which downstream channels activate, giving Opus causal reasoning alongside raw numbers.

## Social Impact

This platform democratizes institutional-grade economic analysis. State treasurers get real-time fiscal dashboards with causal chain explanations instead of quarterly reports. Nonprofits tracking inflation see exactly which CPI components hurt their communities and why. Agricultural cooperatives trace how Fed rate decisions propagate to farm-gate commodity prices. Workforce development agencies identify labor market regime shifts before they become crises. The ontology makes complex economic causality accessible to non-specialists — turning Wall Street expertise into public infrastructure.

## Technology

Claude Opus 4.6, Neo4j (causal ontology, 78 nodes, 120 relationships), FastAPI, React, PyTorch CUDA, Docker, FRED API (127 series), x402 micropayments, human-in-the-loop prompt lifecycle.

## What It Does

8 specialist agents continuously analyze Federal Reserve economic data and Claude Opus 4.6 fuses their signals into actionable intelligence. A Neo4j knowledge graph encodes causal relationships — not just that M2 correlates with BTC (ρ=0.94, 90-day lag), but the transmission mechanism: Fed policy → yield curve → credit spreads → DeFi outflows. When thresholds fire (VIX>30, M2 YoY>4%), the ontology traces which downstream channels activate and injects causal reasoning into the synthesis.

# Webpage
<img width="1321" height="807" alt="Screenshot 2026-02-27 at 4 16 42 PM" src="https://github.com/user-attachments/assets/59e03326-cac3-4147-8eae-8da157d50ab7" />
<img width="1323" height="809" alt="Screenshot 2026-02-27 at 4 16 54 PM" src="https://github.com/user-attachments/assets/7a1d4eed-a49f-4930-bfec-4dca6cbefac0" />
<img width="1321" height="723" alt="Screenshot 2026-02-27 at 4 17 06 PM" src="https://github.com/user-attachments/assets/f8428c3d-f740-479c-87ee-14a41781bc38" />

<img width="1321" height="385" alt="Screenshot 2026-02-27 at 4 17 19 PM" src="https://github.com/user-attachments/assets/0620139f-cfb4-4005-b37a-b41925061751" />
<img width="1324" height="587" alt="Screenshot 2026-02-27 at 4 17 31 PM" src="https://github.com/user-attachments/assets/e38be527-31b9-4dec-9099-ac2c783633d9" />
<img width="1321" height="448" alt="Screenshot 2026-02-27 at 4 17 41 PM" src="https://github.com/user-attachments/assets/917b43df-811e-4e99-b6e1-032e5da09df2" />

<img width="1317" height="474" alt="Screenshot 2026-02-27 at 4 17 52 PM" src="https://github.com/user-attachments/assets/023053b0-b931-4639-ad0d-b8d02165f745" />

<img width="1322" height="591" alt="Screenshot 2026-02-27 at 4 18 00 PM" src="https://github.com/user-attachments/assets/ba4b2b32-6b5d-458d-a611-ecc9e2109e1f" />

# Ontology results : 
The ontology maps how macro signals cascade: Fed policy moves yields (strength 0.95), which shifts credit spreads (7d lag), which triggers DeFi outflows (3d). M2→BTC is the strongest direct channel (ρ=0.94, 90d). VIX>30 fires instant MEV liquidations.

<img width="973" height="616" alt="Screenshot 2026-02-27 at 4 18 24 PM" src="https://github.com/user-attachments/assets/ee5529a3-2277-4e6d-be93-ebaf818025a5" />

## Architecture
<img width="941" height="793" alt="Screenshot 2026-02-27 at 4 25 37 PM" src="https://github.com/user-attachments/assets/15b5aad9-8ef4-488e-aec9-73ad3d9fa442" />

<img width="904" height="399" alt="Screenshot 2026-02-27 at 4 25 53 PM" src="https://github.com/user-attachments/assets/82318e15-4d55-4f43-bcd9-956d47247554" />


```
┌─────────────────────────────────────────────────────────┐
│  ① FRED API (127 series, 15min refresh)                 │
│  ② Anthropic API (Opus 4.6 synthesis, Sonnet classify)  │
│  ③ x402 / Circle (USDC micropayments)                   │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌──────────┬─────────────┬──────────┐
│ backend  │   neo4j     │ frontend │
│ :8000    │   :7687     │ :3000    │
│ FastAPI  │  Ontology   │ React    │
│ 8 agents │  78 nodes   │ 8 tabs   │
│ Opus 4.6 │ 120 rels    │ Recharts │
└──────────┴─────────────┴──────────┘
       │           │
       ▼           ▼
  8 Agents    Causal Chains
       │      Thresholds
       ▼      Transmission
  Opus 4.6 ←── Ontology Context
       │
       ▼
  8 Verticals → Dashboard
```

## 8 Specialist Agents

| Agent | FRED Series | Signal |
|---|---|---|
| Yield Curve | DGS2, DGS10, DGS30, T10Y2Y | Steepening, flattening, inversion |
| Credit Risk | BAA, HY OAS, IG OAS, BAA10Y | Spread widening/tightening |
| Inflation | CPI, PCE, T10YIE, breakevens | Sticky vs transitory, expectations |
| Tail Risk | 30Y-10Y spread percentiles | Extreme term premium moves |
| Cross-Correlation | All series sync analysis | Unified vs divergent policy signals |
| Liquidity | M2, Fed balance sheet, RRP, NFCI | Money supply regime, financial conditions |
| Dollar/Volatility | VIX, DXY, S&P 500 | Risk-on/off, safe haven flows |
| Employment/Stress | UNRATE, ICSA, PAYEMS, STLFSI | Labor market regime, stress indicators |

## 8 Verticals

| Vertical | Series | Audience |
|---|---|---|
| ⚡ DeFi & Crypto | 49 series (PRIMARY) | Crypto funds, DeFi protocols, MEV researchers |
| 🏛️ County GDP & Fiscal | 11 series | State treasurers, muni bond analysts, rating agencies |
| 🏠 Housing & Real Estate | 10 series | Mortgage analysts, FHFA, housing developers |
| 🏪 Small Business | 10 series | SBA, local chambers, small business owners |
| 💰 Inflation & Consumer | 10 series | Nonprofits, consumer advocates, policy makers |
| 🌾 Agriculture & Commodities | 10 series | Farmers, co-ops, commodity traders |
| 🚢 Trade & Supply Chain | 10 series | Trade analysts, manufacturers, logistics |
| 👷 Labor Market | 11 series | Workforce agencies, BLS, HR analytics |

## Neo4j Ontology

The knowledge graph encodes macro economic causality:

**Nodes (78):** 8 Agents, 11 Domains, 8 Verticals, 22 FRED Series, 7 Indicators, 7 Thresholds, 8 Regimes, 7 Transmission Channels

**Key Transmission Channels:**
- M2 → BTC (ρ=0.94, 90-day lag)
- S&P 500 → BTC (ρ=0.80, 24-48hr)
- USD → BTC (ρ=-0.50, inverse, real-time)
- VIX → MEV Liquidation (ρ=0.85, instant)
- Credit → DeFi TVL (ρ=0.65, 3-day lag)
- ISM → Altseason (ρ=0.55, 30-day lag)
- RRP → Stablecoin Supply (ρ=0.70, 14-day lag)

**Causal Chains:**
```
Fed Policy → Yield Curve → Credit → Macro Crypto (10-day lag, strength 0.49)
Liquidity → Macro Crypto (90-day lag, strength 0.94)
Inflation → Fed Policy → Yield Curve (30-day lag, strength 0.85)
```

**Threshold Alerts:**
- VIX > 30 → Risk-Off Panic → MEV liquidation cascades
- M2 YoY > 4% → Crypto Bull Transmission
- M2 YoY < 2% → Crypto Bear (liquidity drought)
- Yield curve slope < 0 → Recession signal
- HY OAS > 500bp → Credit crisis → DeFi TVL outflows

## Prompt Lifecycle

Human-in-the-loop prompt evolution:

```
BOOTSTRAP → DRAFT → EVOLVING (20+ runs) → CURATED (human ✓) → SELF-IMPROVE
```

- Opus writes its own system prompt (bootstrap)
- Auto-promotes after 20 successful runs with confidence > 0.6
- Human reviews, edits, and approves via `/api/prompts/curate`
- Performance tracking: runs, avg confidence, regime changes, conflicts
- Full version history with rollback support

## Project Structure

```
treasury-agent/
├── backend/
│   ├── agents/
│   │   ├── base_agent.py          # Base agent class
│   │   ├── yield_curve.py         # Yield curve regime detection
│   │   ├── credit_risk.py         # Credit spread analysis
│   │   ├── inflation.py           # Inflation expectations
│   │   ├── tail_risk.py           # Long-duration tail risk
│   │   ├── cross_correlation.py   # Cross-series sync
│   │   ├── liquidity.py           # M2/RRP/NFCI analysis
│   │   ├── dollar_vol.py          # USD/VIX regime
│   │   ├── employment.py          # Labor market signals
│   │   └── orchestrator.py        # Opus 4.6 signal fusion
│   ├── api/
│   │   ├── routes.py              # Core API endpoints
│   │   ├── prompt_routes.py       # Prompt lifecycle endpoints
│   │   ├── vertical_routes.py     # Multi-vertical endpoints
│   │   └── ontology_routes.py     # Neo4j ontology endpoints
│   ├── core/
│   │   ├── config.py              # Configuration
│   │   ├── fred_client.py         # FRED API client
│   │   ├── agent_loop.py          # 15-min agent cycle
│   │   ├── prompt_lifecycle.py    # Prompt evolution engine
│   │   └── ontology.py            # Neo4j knowledge graph
│   ├── data/
│   │   ├── series_config.py       # 127 FRED series definitions
│   │   └── verticals.py           # 8 vertical configurations
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Main app with vertical tabs
│   │   ├── components/
│   │   │   ├── VerticalDashboard.jsx  # Generic vertical renderer
│   │   │   ├── PromptReviewPanel.jsx  # Prompt lifecycle UI
│   │   │   └── ...charts
│   │   ├── hooks/
│   │   │   └── useVerticalData.js     # Vertical data fetching
│   │   └── styles/
│   ├── package.json
│   └── index.html
├── docker-compose.yml             # 3 services: backend, frontend, neo4j
├── Dockerfile.backend
└── Dockerfile.frontend
```

## Quick Start

```bash
# 1. Set environment variables
cp .env.example .env
# Edit .env with your FRED_API_KEY and ANTHROPIC_API_KEY

# 2. Start all services
docker compose up -d

# 3. Seed the ontology
curl -X POST http://localhost:8000/api/ontology/seed

# 4. Open the dashboard
open http://localhost:3000
```

## Environment Variables

```
FRED_API_KEY=           # Required — free at https://fred.stlouisfed.org/docs/api/api_key.html
ANTHROPIC_API_KEY=      # Required for Opus synthesis
CLAUDE_MODEL=claude-sonnet-4-20250514
AGENT_LOOP_INTERVAL=900 # 15 minutes
```

## API Endpoints

**Core:**
- `GET /api/health` — Health check
- `GET /api/agents/analyze` — Latest 8-agent synthesis
- `GET /api/data/curve` — Yield curve data
- `GET /api/data/core` — Core series data
- `GET /api/data/extended` — Extended series data
- `WS /ws/agents` — WebSocket live updates

**Verticals:**
- `GET /api/verticals` — List all 8 verticals
- `GET /api/v/{vertical_id}/data` — Vertical-specific data
- `GET /api/v/{vertical_id}/analysis` — Vertical-specific synthesis

**Prompt Lifecycle:**
- `GET /api/prompts/active` — Current active prompt
- `POST /api/prompts/curate` — Approve/edit prompt (human review)
- `POST /api/prompts/rollback` — Rollback to previous version
- `GET /api/prompts/performance` — Prompt performance metrics

**Ontology:**
- `POST /api/ontology/seed` — Build the knowledge graph
- `GET /api/ontology/health` — Neo4j connectivity + node count
- `GET /api/ontology/channels/{regime}` — Active transmission channels
- `POST /api/ontology/causal-chain` — Find causal paths between domains
- `POST /api/ontology/alerts` — Check threshold alerts

## Key Correlations (Encoded in Ontology)

| Channel | ρ | Lag | Mechanism |
|---|---|---|---|
| M2 → BTC | 0.94 | 90 days | Liquidity expansion → portfolio rebalancing → crypto demand |
| S&P → BTC | 0.72-0.87 | 24-48hr | Equity risk-on confirms crypto positioning |
| USD → BTC | ≈ -0.50 | Real-time | Strong dollar = crypto headwind, inverse |
| VIX > 30 | 0.85 | Instant | Panic → cascading DeFi liquidations → MEV extraction spikes |
| Credit → DeFi | 0.65 | 24-72hr | HY spread widening → institutional DeFi withdrawal |
| ISM > 50 | 0.55 | ~30 days | Manufacturing expansion → risk appetite → altseason trigger |

## License

Proprietary — AdaBoost AI
