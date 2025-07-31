from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class TradingConfig:
    """Configuration class for automated trading system"""
    portfolio_value: float = 100000.0
    starting_cash: float = 100000.0
    max_position_size: float = 0.1  # 10% of portfolio
    stop_loss_percentage: float = 0.15  # 15% stop loss
    stop_loss_pct: float = 0.15  # Alias for compatibility
    min_market_cap: float = 10_000_000  # $10M minimum
    max_market_cap: float = 300_000_000  # $300M maximum (micro-cap)
    max_daily_trades: int = 5
    min_volume: int = 100_000  # Minimum daily volume
    risk_tolerance: str = "moderate"
    enable_notifications: bool = True
    
    # File paths
    data_dir: str = "data"
    portfolio_file: str = "chatgpt_portfolio_update.csv"
    trade_log_file: str = "chatgpt_trade_log.csv"
    
    # Trading mode
    paper_trading: bool = True
    
    # Broker configuration
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    
    # AI configuration
    primary_model: str = "gpt-4"
    
    # AI decision parameters
    confidence_threshold: float = 0.7
    sentiment_weight: float = 0.3
    technical_weight: float = 0.4
    fundamental_weight: float = 0.3

# Benchmark tickers for performance comparison
BENCHMARK_TICKERS = [
    "SPY",  # S&P 500
    "IWM",  # Russell 2000 (small caps)
    "VTI",  # Total Stock Market
]

# Days to perform deep research on holdings
DEEP_RESEARCH_DAYS = [1, 7, 30]  # 1 day, 1 week, 1 month intervals
