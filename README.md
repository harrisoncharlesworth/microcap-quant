# Microcap Quant 🚀💎

*Quantitative trading system for micro-cap market opportunities*

## Why Microcap Quant?

The micro-cap universe (sub-$300M market cap) represents the final frontier of market inefficiency. While algorithms dominate large-cap trading, micro-caps remain a playground for informed investors. Microcap Quant combines cutting-edge AI research with systematic execution to capture alpha in this overlooked space.

## 🔥 Core Features

- **Dual-Intelligence Architecture**  
  • **09:30 EST** — OpenAI o3 deep research with real-time web scraping  
  • **16:30 EST** — GPT-4o portfolio optimization and execution signals

- **Professional Risk Management** — Dynamic position sizing, sector limits, volatility-adjusted stops
- **Multi-Provider AI Stack** — OpenAI → Anthropic → Groq with automatic failover
- **Real-Time Execution** — Alpaca integration with paper/live trading modes
- **Comprehensive Analytics** — Performance tracking vs Russell 2000 + sector benchmarks

## ⚡ Quick Start

```bash
git clone https://github.com/harrisoncharlesworth/microcap-quant.git
cd microcap-quant
pip install -r requirements.txt

# Configure your API keys
cp .env.example .env
# Edit .env with your OpenAI + Alpaca credentials

# Test the system
python test_ai_only.py

# Run full cycle
python auto_trader/automated_trader.py run-once
```

## 🏗️ Architecture

```
auto_trader/          # Core trading engine
├── ai_decision_engine.py    # Multi-LLM orchestration
├── automated_trader.py      # Main execution loop
├── risk_gate.py            # Advanced risk controls
└── broker_interface.py     # Alpaca API wrapper

scripts/              # Utilities & visualization
data/                # Portfolio state & trade logs
docs/                # Strategy documentation
reports/             # Research output
```

## 🧠 AI Strategy

**Deep Research Mode (Market Open)**
- SEC filing analysis
- Earnings transcript parsing  
- News sentiment analysis
- Technical pattern recognition
- Sector rotation detection

**Daily Execution Mode (Market Close)**
- Portfolio rebalancing
- Stop-loss management
- Risk-adjusted position sizing
- Performance attribution

## 📊 Performance Tracking

The system automatically generates:
- Daily P&L reports with benchmark comparison
- Weekly research summaries
- Risk metrics (Sharpe, Sortino, Max Drawdown)
- Sector exposure analysis

## ⚙️ Configuration

Key environment variables:
```bash
# AI Models
AI_RESEARCH_MODEL=o3-deep-research-2025-06-26
AI_PRIMARY_MODEL=gpt-4o

# Trading
ALPACA_API_KEY=your_key
PAPER_TRADING=true
MAX_POSITION_PCT=0.15
```

## 🛡️ Risk Controls

- **Position Limits**: 15% max single position
- **Sector Caps**: 40% max sector exposure  
- **Liquidity Filters**: $300K+ average daily volume
- **Market Regime Detection**: Bear market position scaling
- **Circuit Breakers**: 5% daily loss limits

## 📈 Backtesting

Historical performance analysis available via:
```bash
python scripts/backtest_engine.py --start 2024-01-01 --end 2024-12-31
```

## 🤝 Contributing

Microcap Quant is designed for systematic trading research. Contributions welcome:
- New alpha factors
- Risk model improvements  
- Alternative data sources
- Execution optimizations

## ⚠️ Disclaimer

This software is for educational and research purposes. Past performance does not guarantee future results. Trading involves risk of loss. Use at your own discretion.

---

*Built for systematic micro-cap alpha discovery*
