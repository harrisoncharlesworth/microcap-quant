# AGENT.md - ChatGPT Micro-Cap Trading Experiment

## Commands
- **Run trading script**: `python3 "Scripts and CSV Files/Trading_Script.py"` (requires yfinance, pandas, numpy)
- **Generate performance graph**: `python3 "Scripts and CSV Files/Generate_Graph.py"` (requires matplotlib)
- **Install dependencies**: `pip install yfinance pandas numpy matplotlib`

## Architecture
- **Main scripts**: `Scripts and CSV Files/` contains core trading logic and visualization
- **Portfolio data**: `chatgpt_portfolio_update.csv` tracks daily portfolio values and PnL
- **Trade logging**: `chatgpt_trade_log.csv` records all buy/sell transactions
- **Research docs**: `Experiment Details/` contains prompts, Q&A, and research methodology
- **Weekly reports**: Markdown summaries in `Weekly Deep Research (MD)/`, PDFs in `Weekly Deep Research (PDF)/`

## Code Style
- **Variables**: snake_case (e.g., `buy_price`, `total_value`, `stop_loss`)
- **Functions**: snake_case with descriptive names (e.g., `process_portfolio`, `log_manual_buy`)
- **Data handling**: pandas DataFrames for portfolio data, yfinance for market data
- **File paths**: Relative paths from repo root (e.g., `"Scripts and CSV Files/filename.csv"`)
- **Error handling**: Manual confirmation for trades via input() prompts
- **Formatting**: 2-decimal precision for prices/values using round()

## Portfolio Management
- Micro-cap stocks only (market cap under $300M)
- Automated stop-loss triggers via `process_portfolio()`
- Manual buy/sell functions with safety checks
- Daily performance tracking with Sharpe/Sortino ratios
