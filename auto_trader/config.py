"""
Configuration settings for the automated trading system
"""
import os
from dataclasses import dataclass
from typing import List

@dataclass
class TradingConfig:
    # Portfolio settings
    starting_cash: float = 100.0
    max_position_size: float = 0.15  # 15% max per stock
    stop_loss_pct: float = 0.15  # 15% stop loss
    max_daily_loss: float = 0.05  # 5% daily circuit breaker
    
    # Trading universe
    market_cap_max: float = 300_000_000  # $300M max market cap
    min_volume: float = 50_000  # $50k daily volume minimum
    
    # AI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    primary_model: str = os.getenv("AI_PRIMARY_MODEL", "gpt-4o")  # 16:30 cycle
    backup_model: str = os.getenv("AI_BACKUP_MODEL", "gpt-4")  # fallback
    deep_research_model: str = os.getenv("AI_RESEARCH_MODEL", "o3-deep-research-2025-06-26")  # 09:30 cycle
    
    # Broker settings
    alpaca_api_key: str = os.getenv("ALPACA_API_KEY", "")
    alpaca_secret_key: str = os.getenv("ALPACA_SECRET_KEY", "")
    paper_trading: bool = True
    
    # Scheduling
    trading_time: str = "16:30"  # Run 30min after market close EST
    pre_market_research_time: str = "07:45"  # Deep research 90min before market open
    intraday_news_time: str = "11:00"  # Optional news refresh mid-day
    timezone: str = "US/Eastern"
    
    # Monitoring
    slack_webhook: str = os.getenv("SLACK_WEBHOOK", "")
    email_alerts: bool = True
    email_to: str = os.getenv("EMAIL_TO", "")
    email_from: str = os.getenv("EMAIL_FROM", "")
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", os.getenv("EMAIL_FROM", ""))
    smtp_password: str = os.getenv("SMTP_PASSWORD", os.getenv("EMAIL_PASSWORD", ""))
    
    # Data storage
    data_dir: str = "data"
    portfolio_file: str = "chatgpt_portfolio_update.csv"
    trade_log_file: str = "chatgpt_trade_log.csv"

# Watchlist tickers for comparison
BENCHMARK_TICKERS = ["^RUT", "IWO", "XBI"]

# Daily deep research schedule  
DEEP_RESEARCH_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]  # Run daily pre-market research
