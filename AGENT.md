# AGENT.md - Micro-Cap Quantitative Trading

## Commands
- **Run trading script**: `python3 scripts/Trading_Script.py` (requires yfinance, pandas, numpy)
- **Generate performance graph**: `python3 scripts/Generate_Graph.py` (requires matplotlib)
- **Install dependencies**: `pip install -r requirements.txt`

## Architecture
- **Main scripts**: `scripts/` contains core trading logic and visualization
- **Portfolio data**: `data/chatgpt_portfolio_update.csv` tracks daily portfolio values and PnL
- **Trade logging**: `data/chatgpt_trade_log.csv` records all buy/sell transactions
- **Research docs**: `docs/` contains prompts, Q&A, and research methodology
- **Weekly reports**: Markdown summaries in `reports/markdown/`, PDFs in `reports/pdf/`

## Code Style
- **Variables**: snake_case (e.g., `buy_price`, `total_value`, `stop_loss`)
- **Functions**: snake_case with descriptive names (e.g., `process_portfolio`, `log_manual_buy`)
- **Data handling**: pandas DataFrames for portfolio data, yfinance for market data
- **File paths**: Relative paths from repo root (e.g., `"data/filename.csv"`)
- **Error handling**: Manual confirmation for trades via input() prompts
- **Formatting**: 2-decimal precision for prices/values using round()

## Portfolio Management
- Micro-cap stocks only (market cap under $300M)
- Automated stop-loss triggers via `process_portfolio()`
- Manual buy/sell functions with safety checks
- Daily performance tracking with Sharpe/Sortino ratios
