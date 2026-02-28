"""
Vertical Registry — 8 macro intelligence verticals.

Each vertical defines:
  - FRED series to fetch
  - Chart configurations for the dashboard
  - KPI definitions
  - System prompt template for Opus 4.6 synthesis
  - Target customers and pricing
"""

VERTICALS = {

    # ═══════════════════════════════════════════════════════════════════
    #  1. DeFi / Crypto (PRIMARY — the original 8-agent system)
    # ═══════════════════════════════════════════════════════════════════
    "defi_crypto": {
        "id": "defi_crypto",
        "name": "DeFi & Crypto",
        "icon": "⚡",
        "color": "#06b6d4",
        "is_primary": True,
        "description": "Macro→DeFi transmission: M2→BTC correlation, MEV liquidation triggers, yield farming risk",
        "tagline": "8 Agents · 49 FRED Series · Macro→Crypto Transmission Channels",
        "customers": ["Crypto funds", "DeFi protocols", "MEV researchers", "Institutional OTC desks"],
        "uses_primary_agents": True,
        "series": [],
        "charts": [],
        "kpis": [],
    },

    # ═══════════════════════════════════════════════════════════════════
    #  2. County-Level GDP & Fiscal Analysis
    # ═══════════════════════════════════════════════════════════════════
    "county_fiscal": {
        "id": "county_fiscal",
        "name": "County GDP & Fiscal",
        "icon": "🏛️",
        "color": "#8b5cf6",
        "is_primary": False,
        "description": "County-level GDP, government expenditure, fiscal health, property tax trends",
        "tagline": "Municipal Fiscal Intelligence · State & County Economics",
        "customers": ["Municipal bond analysts", "State treasurers", "Local government planners", "Rating agencies"],
        "series": [
            {"id": "GDP", "name": "US GDP", "freq": "Quarterly", "units": "Billions USD"},
            {"id": "A191RL1Q225SBEA", "name": "Real GDP Growth (QoQ Annualized)", "freq": "Quarterly", "units": "Percent"},
            {"id": "GFDEBTN", "name": "Federal Debt Total", "freq": "Quarterly", "units": "Millions USD"},
            {"id": "FYFSD", "name": "Federal Surplus/Deficit", "freq": "Annual", "units": "Millions USD"},
            {"id": "SLEXPND", "name": "State & Local Gov Expenditure", "freq": "Quarterly", "units": "Billions USD"},
            {"id": "FGEXPND", "name": "Federal Gov Expenditure", "freq": "Quarterly", "units": "Billions USD"},
            {"id": "W006RC1Q027SBEA", "name": "Gov Investment (Gross)", "freq": "Quarterly", "units": "Billions USD"},
            {"id": "A822RL1Q225SBEA", "name": "State & Local Gov Spending (Real)", "freq": "Quarterly", "units": "Percent"},
            {"id": "B094RC1Q027SBEA", "name": "Personal Tax Revenue", "freq": "Quarterly", "units": "Billions USD"},
            {"id": "FGRECPT", "name": "Federal Gov Receipts", "freq": "Quarterly", "units": "Billions USD"},
            {"id": "W068RCQ027SBEA", "name": "Gov Social Benefits", "freq": "Quarterly", "units": "Billions USD"},
        ],
        "kpis": [
            {"series_id": "A191RL1Q225SBEA", "label": "GDP Growth", "color": "#8b5cf6", "format": ".1f", "suffix": "%"},
            {"series_id": "GFDEBTN", "label": "Federal Debt", "color": "#ef4444", "format": ",.0f", "suffix": "M"},
            {"series_id": "SLEXPND", "label": "State/Local Spend", "color": "#f59e0b", "format": ",.0f", "suffix": "B"},
            {"series_id": "FGRECPT", "label": "Fed Receipts", "color": "#22c55e", "format": ",.0f", "suffix": "B"},
            {"series_id": "FYFSD", "label": "Surplus/Deficit", "color": "#f87171", "format": ",.0f", "suffix": "M"},
        ],
        "charts": [
            {"chart_id": "gdp_growth", "title": "Real GDP Growth (QoQ Annualized)", "series": ["A191RL1Q225SBEA"], "chart_type": "area", "color": "#8b5cf6", "reference_lines": {"0": "Zero Growth", "2": "Trend (2%)", "-2": "Contraction"}},
            {"chart_id": "federal_debt", "title": "Federal Debt Outstanding", "series": ["GFDEBTN"], "chart_type": "area", "color": "#ef4444"},
            {"chart_id": "gov_spending", "title": "Government Expenditure: Federal vs State/Local", "series": ["FGEXPND", "SLEXPND"], "chart_type": "line", "color": "#f59e0b"},
            {"chart_id": "fiscal_balance", "title": "Federal Receipts vs Expenditure", "series": ["FGRECPT", "FGEXPND"], "chart_type": "line", "color": "#22c55e"},
            {"chart_id": "tax_revenue", "title": "Personal Tax Revenue", "series": ["B094RC1Q027SBEA"], "chart_type": "area", "color": "#60a5fa"},
            {"chart_id": "social_benefits", "title": "Government Social Benefits Spending", "series": ["W068RCQ027SBEA"], "chart_type": "area", "color": "#ec4899"},
        ],
        "prompt_template": "You are a municipal fiscal analyst. Analyze GDP growth, federal debt trajectory, spending vs revenue, state/local fiscal health. Focus on: fiscal sustainability, debt/GDP trend, tax base health, social obligations growth, recession vulnerability. Respond in JSON: market_regime, regime_label, dominant_signal, confidence, headline, narrative, key_risks, regime_triggers.",
    },

    # ═══════════════════════════════════════════════════════════════════
    #  3. Housing Market Risk
    # ═══════════════════════════════════════════════════════════════════
    "housing": {
        "id": "housing",
        "name": "Housing & Real Estate",
        "icon": "🏠",
        "color": "#f59e0b",
        "is_primary": False,
        "description": "Home prices, mortgage rates, housing starts, inventory — bubble detection and market health",
        "tagline": "Case-Shiller · Mortgage Rates · Supply/Demand · Affordability",
        "customers": ["REITs", "Mortgage lenders", "Real estate funds", "Home builders", "Insurance cos"],
        "series": [
            {"id": "CSUSHPISA", "name": "Case-Shiller US Home Price Index", "freq": "Monthly", "units": "Index"},
            {"id": "MORTGAGE30US", "name": "30-Year Fixed Mortgage Rate", "freq": "Weekly", "units": "Percent"},
            {"id": "MORTGAGE15US", "name": "15-Year Fixed Mortgage Rate", "freq": "Weekly", "units": "Percent"},
            {"id": "HOUST", "name": "Housing Starts", "freq": "Monthly", "units": "Thousands"},
            {"id": "PERMIT", "name": "Building Permits", "freq": "Monthly", "units": "Thousands"},
            {"id": "MSACSR", "name": "Monthly Supply of New Houses", "freq": "Monthly", "units": "Months"},
            {"id": "EXHOSLUSM495S", "name": "Existing Home Sales", "freq": "Monthly", "units": "Millions"},
            {"id": "MSPUS", "name": "Median Home Sale Price", "freq": "Quarterly", "units": "USD"},
            {"id": "RRVRUSQ156N", "name": "Rental Vacancy Rate", "freq": "Quarterly", "units": "Percent"},
            {"id": "MDSP", "name": "Household Debt Service Ratio", "freq": "Quarterly", "units": "Percent"},
        ],
        "kpis": [
            {"series_id": "MORTGAGE30US", "label": "30Y Mortgage", "color": "#ef4444", "format": ".2f", "suffix": "%"},
            {"series_id": "CSUSHPISA", "label": "Case-Shiller", "color": "#f59e0b", "format": ".1f", "suffix": ""},
            {"series_id": "HOUST", "label": "Housing Starts", "color": "#22c55e", "format": ",.0f", "suffix": "K"},
            {"series_id": "MSACSR", "label": "Months Supply", "color": "#60a5fa", "format": ".1f", "suffix": " mo"},
            {"series_id": "MSPUS", "label": "Median Price", "color": "#8b5cf6", "format": ",.0f", "suffix": ""},
        ],
        "charts": [
            {"chart_id": "mortgage_rates", "title": "Mortgage Rates (30Y & 15Y)", "series": ["MORTGAGE30US", "MORTGAGE15US"], "chart_type": "line", "color": "#ef4444", "reference_lines": {"7": "Affordability Stress", "5": "Normal"}},
            {"chart_id": "home_prices", "title": "Case-Shiller US Home Price Index", "series": ["CSUSHPISA"], "chart_type": "area", "color": "#f59e0b"},
            {"chart_id": "supply_demand", "title": "Housing Starts vs Building Permits", "series": ["HOUST", "PERMIT"], "chart_type": "line", "color": "#22c55e"},
            {"chart_id": "inventory", "title": "Months Supply of New Houses", "series": ["MSACSR"], "chart_type": "area", "color": "#60a5fa", "reference_lines": {"6": "Balanced", "4": "Tight Supply"}},
            {"chart_id": "sales_volume", "title": "Existing Home Sales", "series": ["EXHOSLUSM495S"], "chart_type": "area", "color": "#8b5cf6"},
            {"chart_id": "debt_service", "title": "Household Debt Service Ratio", "series": ["MDSP"], "chart_type": "line", "color": "#ec4899", "reference_lines": {"13": "Pre-2008 Stress"}},
        ],
        "prompt_template": "You are a housing market strategist. Analyze mortgage rates, home prices, supply/demand, affordability. Mortgage >7% = freeze. Months supply >6 = buyer's market, <4 = bubble risk. Starts declining 3+ months = recession lead (6-9mo). Debt service >13% = pre-2008 stress. Respond in JSON: market_regime, headline, narrative, key_risks, regime_triggers.",
    },

    # ═══════════════════════════════════════════════════════════════════
    #  4. Small Business / Main Street Economy
    # ═══════════════════════════════════════════════════════════════════
    "small_business": {
        "id": "small_business",
        "name": "Small Business & Main Street",
        "icon": "🏪",
        "color": "#22c55e",
        "is_primary": False,
        "description": "NFIB optimism, consumer credit, retail sales, savings rate — Main Street economic health",
        "tagline": "NFIB Optimism · Consumer Credit · Retail Sales · Lending",
        "customers": ["SBA", "Chambers of commerce", "Fintech lenders", "Community banks"],
        "series": [
            {"id": "RSAFS", "name": "Retail Sales (Total)", "freq": "Monthly", "units": "Millions USD"},
            {"id": "TOTALSL", "name": "Total Consumer Credit", "freq": "Monthly", "units": "Billions USD"},
            {"id": "REVOLSL", "name": "Revolving Credit (Credit Cards)", "freq": "Monthly", "units": "Billions USD"},
            {"id": "UMCSENT", "name": "UMich Consumer Sentiment", "freq": "Monthly", "units": "Index"},
            {"id": "PCE", "name": "Personal Consumption Expenditure", "freq": "Monthly", "units": "Billions USD"},
            {"id": "PSAVERT", "name": "Personal Savings Rate", "freq": "Monthly", "units": "Percent"},
            {"id": "DRCCLACBS", "name": "Credit Card Delinquency Rate", "freq": "Quarterly", "units": "Percent"},
            {"id": "BUSLOANS", "name": "Commercial & Industrial Loans", "freq": "Monthly", "units": "Billions USD"},
            {"id": "AWHNONAG", "name": "Avg Weekly Hours (All Private)", "freq": "Monthly", "units": "Hours"},
            {"id": "INDPRO", "name": "Industrial Production Index", "freq": "Monthly", "units": "Index"},
        ],
        "kpis": [
            {"series_id": "UMCSENT", "label": "Consumer Sent.", "color": "#22c55e", "format": ".1f", "suffix": ""},
            {"series_id": "PSAVERT", "label": "Savings Rate", "color": "#f59e0b", "format": ".1f", "suffix": "%"},
            {"series_id": "RSAFS", "label": "Retail Sales", "color": "#8b5cf6", "format": ",.0f", "suffix": "M"},
            {"series_id": "DRCCLACBS", "label": "CC Delinquency", "color": "#ef4444", "format": ".2f", "suffix": "%"},
            {"series_id": "BUSLOANS", "label": "C&I Loans", "color": "#60a5fa", "format": ",.0f", "suffix": "B"},
        ],
        "charts": [
            {"chart_id": "consumer_sentiment", "title": "UMich Consumer Sentiment", "series": ["UMCSENT"], "chart_type": "area", "color": "#22c55e", "reference_lines": {"80": "Neutral", "60": "Recession Level"}},
            {"chart_id": "retail_sales", "title": "Total Retail Sales", "series": ["RSAFS"], "chart_type": "area", "color": "#8b5cf6"},
            {"chart_id": "consumer_credit", "title": "Consumer Credit: Total vs Revolving", "series": ["TOTALSL", "REVOLSL"], "chart_type": "line", "color": "#f59e0b"},
            {"chart_id": "savings_rate", "title": "Personal Savings Rate", "series": ["PSAVERT"], "chart_type": "area", "color": "#14b8a6", "reference_lines": {"8": "Healthy", "3": "Stress"}},
            {"chart_id": "business_loans", "title": "Commercial & Industrial Loans", "series": ["BUSLOANS"], "chart_type": "area", "color": "#ec4899"},
            {"chart_id": "industrial_prod", "title": "Industrial Production Index", "series": ["INDPRO"], "chart_type": "line", "color": "#60a5fa"},
        ],
        "prompt_template": "You are a Main Street economist writing for small business owners. Savings <3% = stress. CC delinquency rising + savings falling = consumer stress. Retail sales declining 2+ months = demand destruction. Weekly hours declining = leading layoff indicator. Write for a restaurant owner, not Wall Street. Respond in JSON: market_regime, headline, narrative, key_risks, regime_triggers.",
    },

    # ═══════════════════════════════════════════════════════════════════
    #  5. Inflation Impact by Income
    # ═══════════════════════════════════════════════════════════════════
    "inflation_impact": {
        "id": "inflation_impact",
        "name": "Inflation & Consumer Impact",
        "icon": "💰",
        "color": "#ef4444",
        "is_primary": False,
        "description": "CPI components breakdown — food, shelter, energy, medical. Who is actually hurting?",
        "tagline": "CPI Components · Real Wages · Purchasing Power · Inequality",
        "customers": ["Policy think tanks", "Congressional offices", "Nonprofits", "Media"],
        "series": [
            {"id": "CPIAUCSL", "name": "CPI All Urban Consumers", "freq": "Monthly", "units": "Index"},
            {"id": "CPIFABSL", "name": "CPI Food at Home", "freq": "Monthly", "units": "Index"},
            {"id": "CPIENGSL", "name": "CPI Energy", "freq": "Monthly", "units": "Index"},
            {"id": "CUSR0000SAH1", "name": "CPI Shelter", "freq": "Monthly", "units": "Index"},
            {"id": "CUSR0000SAM2", "name": "CPI Medical Care Services", "freq": "Monthly", "units": "Index"},
            {"id": "CUUR0000SETB01", "name": "CPI Gasoline", "freq": "Monthly", "units": "Index"},
            {"id": "CES0500000003", "name": "Avg Hourly Earnings (All Private)", "freq": "Monthly", "units": "USD"},
            {"id": "LES1252881600Q", "name": "Median Weekly Earnings", "freq": "Quarterly", "units": "USD"},
            {"id": "DSPIC96", "name": "Real Disposable Personal Income", "freq": "Monthly", "units": "Billions USD"},
            {"id": "CPALTT01USM657N", "name": "CPI Total (YoY Change)", "freq": "Monthly", "units": "Percent"},
        ],
        "kpis": [
            {"series_id": "CPALTT01USM657N", "label": "CPI YoY", "color": "#ef4444", "format": ".1f", "suffix": "%"},
            {"series_id": "CES0500000003", "label": "Avg Hourly Wage", "color": "#22c55e", "format": ".2f", "suffix": ""},
            {"series_id": "CPIFABSL", "label": "Food CPI", "color": "#f59e0b", "format": ".1f", "suffix": ""},
            {"series_id": "CUSR0000SAH1", "label": "Shelter CPI", "color": "#8b5cf6", "format": ".1f", "suffix": ""},
            {"series_id": "CPIENGSL", "label": "Energy CPI", "color": "#06b6d4", "format": ".1f", "suffix": ""},
        ],
        "charts": [
            {"chart_id": "headline_cpi", "title": "CPI Year-over-Year Change", "series": ["CPALTT01USM657N"], "chart_type": "area", "color": "#ef4444", "reference_lines": {"2": "Fed Target", "5": "High", "8": "Crisis"}},
            {"chart_id": "cpi_components", "title": "CPI: Food vs Shelter vs Energy", "series": ["CPIFABSL", "CUSR0000SAH1", "CPIENGSL"], "chart_type": "line", "color": "#f59e0b"},
            {"chart_id": "food_gasoline", "title": "Food vs Gasoline (Essentials Squeeze)", "series": ["CPIFABSL", "CUUR0000SETB01"], "chart_type": "line", "color": "#ec4899"},
            {"chart_id": "real_wages", "title": "Average Hourly Earnings", "series": ["CES0500000003"], "chart_type": "area", "color": "#22c55e"},
            {"chart_id": "real_income", "title": "Real Disposable Personal Income", "series": ["DSPIC96"], "chart_type": "area", "color": "#60a5fa"},
            {"chart_id": "medical", "title": "Medical Care Services CPI", "series": ["CUSR0000SAM2"], "chart_type": "area", "color": "#8b5cf6"},
        ],
        "prompt_template": "You are a social economist explaining inflation's REAL impact by income group. Low-income spend 35% on food+energy vs 15% for high-income. Shelter hits renters (40% of Americans). Use dollar amounts not just percentages. Who is hurting most? Are wages keeping up? What should Congress worry about? Respond in JSON: market_regime, headline, narrative, key_risks, regime_triggers.",
    },

    # ═══════════════════════════════════════════════════════════════════
    #  6. Agriculture & Commodities
    # ═══════════════════════════════════════════════════════════════════
    "agriculture": {
        "id": "agriculture",
        "name": "Agriculture & Commodities",
        "icon": "🌾",
        "color": "#84cc16",
        "is_primary": False,
        "description": "Commodity prices, farm PPI, trade balance, supply chain — rural economic health",
        "tagline": "Commodity Prices · Farm Income · Export Markets · Supply Chain",
        "customers": ["Ag lenders", "Commodity traders", "USDA contractors", "Farm bureaus"],
        "series": [
            {"id": "DCOILWTICO", "name": "WTI Crude Oil Price", "freq": "Daily", "units": "USD/Barrel"},
            {"id": "GOLDAMGBD228NLBM", "name": "Gold Price (London Fix)", "freq": "Daily", "units": "USD/Troy Oz"},
            {"id": "GASREGW", "name": "Regular Gas Price", "freq": "Weekly", "units": "USD/Gallon"},
            {"id": "WPU0223", "name": "PPI Farm Products", "freq": "Monthly", "units": "Index"},
            {"id": "PPIACO", "name": "PPI All Commodities", "freq": "Monthly", "units": "Index"},
            {"id": "BOPGSTB", "name": "Trade Balance", "freq": "Monthly", "units": "Millions USD"},
            {"id": "IQ", "name": "Imports of Goods", "freq": "Monthly", "units": "Billions USD"},
            {"id": "IEABC", "name": "Exports of Goods", "freq": "Monthly", "units": "Billions USD"},
            {"id": "PCOPPUSDM", "name": "Copper Price", "freq": "Monthly", "units": "USD/Metric Ton"},
            {"id": "DTWEXBGS", "name": "USD Index (Broad)", "freq": "Daily", "units": "Index"},
        ],
        "kpis": [
            {"series_id": "DCOILWTICO", "label": "WTI Crude", "color": "#84cc16", "format": ".2f", "suffix": ""},
            {"series_id": "GOLDAMGBD228NLBM", "label": "Gold", "color": "#f59e0b", "format": ",.0f", "suffix": ""},
            {"series_id": "GASREGW", "label": "Gas Price", "color": "#ef4444", "format": ".2f", "suffix": "/gal"},
            {"series_id": "BOPGSTB", "label": "Trade Balance", "color": "#60a5fa", "format": ",.0f", "suffix": "M"},
            {"series_id": "PCOPPUSDM", "label": "Copper", "color": "#ec4899", "format": ",.0f", "suffix": ""},
        ],
        "charts": [
            {"chart_id": "oil", "title": "WTI Crude Oil Price", "series": ["DCOILWTICO"], "chart_type": "area", "color": "#84cc16", "reference_lines": {"80": "Budget Breakeven", "100": "Inflation Pressure"}},
            {"chart_id": "gold", "title": "Gold Price (USD/Troy Oz)", "series": ["GOLDAMGBD228NLBM"], "chart_type": "area", "color": "#f59e0b"},
            {"chart_id": "farm_ppi", "title": "PPI: Farm Products vs All Commodities", "series": ["WPU0223", "PPIACO"], "chart_type": "line", "color": "#22c55e"},
            {"chart_id": "trade", "title": "US Trade Balance", "series": ["BOPGSTB"], "chart_type": "area", "color": "#ef4444", "reference_lines": {"0": "Balanced"}},
            {"chart_id": "imports_exports", "title": "Imports vs Exports", "series": ["IQ", "IEABC"], "chart_type": "line", "color": "#60a5fa"},
            {"chart_id": "copper", "title": "Copper (Dr. Copper — Growth Proxy)", "series": ["PCOPPUSDM"], "chart_type": "area", "color": "#ec4899"},
        ],
        "prompt_template": "You are an agricultural economist. Oil >$100 = farm input cost pressure. Gold surging = macro fear. Copper rising = global growth. Farm PPI diverging from headline = margin compression. Gas >$4/gal = rural stress. Trade deficit widening = dollar weakness = commodity price rise. Respond in JSON: market_regime, headline, narrative, key_risks, regime_triggers.",
    },

    # ═══════════════════════════════════════════════════════════════════
    #  7. Trade & Supply Chain
    # ═══════════════════════════════════════════════════════════════════
    "trade_supply": {
        "id": "trade_supply",
        "name": "Trade & Supply Chain",
        "icon": "🚢",
        "color": "#0ea5e9",
        "is_primary": False,
        "description": "Trade balance, manufacturing, capacity utilization, new orders — supply chain intelligence",
        "tagline": "Global Trade · Manufacturing · Capacity · Orders Pipeline",
        "customers": ["Supply chain teams", "Trade policy analysts", "Logistics cos", "Importers/exporters"],
        "series": [
            {"id": "BOPGSTB", "name": "Trade Balance (G&S)", "freq": "Monthly", "units": "Millions USD"},
            {"id": "BOPGTB", "name": "Trade Balance (Goods)", "freq": "Monthly", "units": "Millions USD"},
            {"id": "IMPGS", "name": "Imports of G&S", "freq": "Quarterly", "units": "Billions USD"},
            {"id": "EXPGS", "name": "Exports of G&S", "freq": "Quarterly", "units": "Billions USD"},
            {"id": "MANEMP", "name": "Manufacturing Employment", "freq": "Monthly", "units": "Thousands"},
            {"id": "IPMAN", "name": "Industrial Production (Mfg)", "freq": "Monthly", "units": "Index"},
            {"id": "TCU", "name": "Capacity Utilization", "freq": "Monthly", "units": "Percent"},
            {"id": "NEWORDER", "name": "Manufacturers New Orders", "freq": "Monthly", "units": "Millions USD"},
            {"id": "AMTMNO", "name": "Manufacturers Total Orders", "freq": "Monthly", "units": "Millions USD"},
            {"id": "DTWEXBGS", "name": "Trade-Weighted USD", "freq": "Daily", "units": "Index"},
        ],
        "kpis": [
            {"series_id": "BOPGSTB", "label": "Trade Balance", "color": "#0ea5e9", "format": ",.0f", "suffix": "M"},
            {"series_id": "IPMAN", "label": "Mfg Production", "color": "#22c55e", "format": ".1f", "suffix": ""},
            {"series_id": "TCU", "label": "Capacity Util.", "color": "#f59e0b", "format": ".1f", "suffix": "%"},
            {"series_id": "MANEMP", "label": "Mfg Jobs", "color": "#8b5cf6", "format": ",.0f", "suffix": "K"},
            {"series_id": "DTWEXBGS", "label": "USD Index", "color": "#ef4444", "format": ".1f", "suffix": ""},
        ],
        "charts": [
            {"chart_id": "trade_bal", "title": "US Trade Balance (G&S)", "series": ["BOPGSTB"], "chart_type": "area", "color": "#0ea5e9", "reference_lines": {"0": "Balanced"}},
            {"chart_id": "imp_exp", "title": "Imports vs Exports (Quarterly)", "series": ["IMPGS", "EXPGS"], "chart_type": "line", "color": "#22c55e"},
            {"chart_id": "mfg", "title": "Industrial Production (Manufacturing)", "series": ["IPMAN"], "chart_type": "area", "color": "#f59e0b"},
            {"chart_id": "capacity", "title": "Capacity Utilization", "series": ["TCU"], "chart_type": "line", "color": "#8b5cf6", "reference_lines": {"80": "High", "75": "Normal", "70": "Slack"}},
            {"chart_id": "orders", "title": "Manufacturers New Orders", "series": ["NEWORDER"], "chart_type": "area", "color": "#ec4899"},
            {"chart_id": "usd", "title": "Trade-Weighted USD", "series": ["DTWEXBGS"], "chart_type": "line", "color": "#ef4444"},
        ],
        "prompt_template": "You are a trade and supply chain analyst. Strong USD = exports suffer but imports cheaper. Capacity >80% = supply constraint = inflation. New orders declining 3+ months = mfg recession. Trade deficit widening = USD weakness = imported inflation. Respond in JSON: market_regime, headline, narrative, key_risks, regime_triggers.",
    },

    # ═══════════════════════════════════════════════════════════════════
    #  8. Labor Market & Workforce
    # ═══════════════════════════════════════════════════════════════════
    "labor_market": {
        "id": "labor_market",
        "name": "Labor Market & Workforce",
        "icon": "👷",
        "color": "#ec4899",
        "is_primary": False,
        "description": "JOLTS openings, quits rate, wages, unemployment by demographic — workforce strategy",
        "tagline": "JOLTS · Quits Rate · Wage Growth · Demographics · Claims",
        "customers": ["Large employers", "Staffing firms", "HR tech companies", "Workforce boards"],
        "series": [
            {"id": "JTSJOL", "name": "JOLTS Job Openings", "freq": "Monthly", "units": "Thousands"},
            {"id": "JTSQUR", "name": "JOLTS Quits Rate", "freq": "Monthly", "units": "Percent"},
            {"id": "JTSHIR", "name": "JOLTS Hires", "freq": "Monthly", "units": "Thousands"},
            {"id": "UNRATE", "name": "Unemployment Rate", "freq": "Monthly", "units": "Percent"},
            {"id": "LNS14000006", "name": "Unemployment (Black)", "freq": "Monthly", "units": "Percent"},
            {"id": "LNS14000009", "name": "Unemployment (Hispanic)", "freq": "Monthly", "units": "Percent"},
            {"id": "PAYEMS", "name": "Total Non-Farm Payrolls", "freq": "Monthly", "units": "Thousands"},
            {"id": "CES0500000003", "name": "Avg Hourly Earnings", "freq": "Monthly", "units": "USD"},
            {"id": "CIVPART", "name": "Labor Force Participation", "freq": "Monthly", "units": "Percent"},
            {"id": "ICSA", "name": "Initial Jobless Claims", "freq": "Weekly", "units": "Number"},
            {"id": "U6RATE", "name": "U-6 Underemployment", "freq": "Monthly", "units": "Percent"},
        ],
        "kpis": [
            {"series_id": "UNRATE", "label": "Unemployment", "color": "#ec4899", "format": ".1f", "suffix": "%"},
            {"series_id": "JTSJOL", "label": "Job Openings", "color": "#22c55e", "format": ",.0f", "suffix": "K"},
            {"series_id": "JTSQUR", "label": "Quits Rate", "color": "#f59e0b", "format": ".1f", "suffix": "%"},
            {"series_id": "CIVPART", "label": "Participation", "color": "#60a5fa", "format": ".1f", "suffix": "%"},
            {"series_id": "CES0500000003", "label": "Avg Hourly Wage", "color": "#8b5cf6", "format": ".2f", "suffix": ""},
        ],
        "charts": [
            {"chart_id": "openings", "title": "JOLTS Job Openings", "series": ["JTSJOL"], "chart_type": "area", "color": "#22c55e"},
            {"chart_id": "quits", "title": "Quits Rate (Worker Confidence)", "series": ["JTSQUR"], "chart_type": "line", "color": "#f59e0b", "reference_lines": {"3.0": "Great Resignation", "2.0": "Normal", "1.5": "Fear"}},
            {"chart_id": "unemp_demo", "title": "Unemployment: Overall vs Black vs Hispanic", "series": ["UNRATE", "LNS14000006", "LNS14000009"], "chart_type": "line", "color": "#ec4899"},
            {"chart_id": "payrolls", "title": "Total Non-Farm Payrolls", "series": ["PAYEMS"], "chart_type": "area", "color": "#60a5fa"},
            {"chart_id": "participation", "title": "Labor Force Participation Rate", "series": ["CIVPART"], "chart_type": "line", "color": "#8b5cf6", "reference_lines": {"63": "Pre-COVID", "62": "Current"}},
            {"chart_id": "claims", "title": "Initial Jobless Claims (Weekly)", "series": ["ICSA"], "chart_type": "area", "color": "#ef4444", "reference_lines": {"300000": "Recession Signal", "200000": "Healthy"}},
        ],
        "prompt_template": "You are a workforce strategist for CHROs and staffing firms. Quits >3% = wage pressure. Quits <2% = layoff cycle. Claims >300K = recession. Participation declining = structural shortage. Hours declining before payrolls = cut hours then heads. Which industries face shortages? Where will wages spike? Respond in JSON: market_regime, headline, narrative, key_risks, regime_triggers.",
    },
}


def get_vertical(vid: str) -> dict:
    return VERTICALS.get(vid)

def list_verticals() -> list[dict]:
    return [
        {"id": v["id"], "name": v["name"], "icon": v["icon"], "color": v["color"],
         "is_primary": v.get("is_primary", False), "description": v["description"],
         "series_count": len(v.get("series", [])) or 49, "chart_count": len(v.get("charts", [])) or 12}
        for v in VERTICALS.values()
    ]

def get_all_series_ids(vid: str) -> list[str]:
    v = VERTICALS.get(vid)
    return [s["id"] for s in v.get("series", [])] if v else []

def get_prompt_template(vid: str) -> str:
    v = VERTICALS.get(vid)
    return v.get("prompt_template", "") if v else ""
