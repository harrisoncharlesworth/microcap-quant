# Micro-Cap Quantitative Trading

AI-powered micro-cap stock trading system with automated portfolio management and performance tracking.

## Overview

This project implements an AI-driven trading system focused on micro-cap stocks (market cap under $300M). The system uses real-time data analysis and automated decision-making to manage a live trading portfolio.

## Features

- **Dual AI Scheduling**: OpenAI o3 deep research at market open + GPT-4o daily analysis
- **Deep Research Integration**: Comprehensive market analysis with web search and financial data
- **Automated Trading Logic**: Daily portfolio evaluation and trade execution
- **Risk Management**: Built-in stop-loss triggers and position sizing
- **Performance Tracking**: Comprehensive logging of trades and portfolio metrics
- **Multi-Provider AI**: OpenAI, Anthropic, Groq support with automatic fallback
- **Visualization**: Performance charts comparing against market indices

## Documentation

- [Research Index](docs/Deep_Research_Index.md)
- [Q&A](docs/QA.md)
- [Trading Prompts](docs/Prompts.md)
- [Weekly Research Reports (MD)](reports/markdown/)
- [Weekly Research Reports (PDF)](reports/pdf/)
  
## Performance

![Performance Chart](performance-chart.png)

The system's performance is tracked against major indices and documented in regular reports.

## AI Trading Cycles

The system runs two automated AI cycles daily:

- **09:30 EST - Market Open**: OpenAI o3 deep research with web search, financial analysis, and comprehensive market research
- **16:30 EST - Market Close**: GPT-4o daily portfolio evaluation, risk management, and trading decisions

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Trading Script**
   ```bash
   python scripts/trading_script.py
   ```

3. **Generate Performance Chart**
   ```bash
   python scripts/generate_graph.py
   ```

## Tech Stack

- **Python**: Core trading logic and data processing
- **pandas**: Data manipulation and analysis
- **yfinance**: Real-time market data
- **matplotlib**: Performance visualization
- **AI Integration**: Automated decision-making system

## Project Structure

```
├── scripts/           # Core trading and visualization scripts
├── data/             # Portfolio and trade data (CSV files)
├── docs/             # Documentation and research
├── reports/          # Weekly analysis reports
└── auto_trader/      # Automated trading components
```

## Contributing

This project serves as a framework for AI-driven trading research. Feel free to fork and adapt for your own experiments.
