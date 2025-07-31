#!/usr/bin/env python3
"""
Automated Micro-Cap Trading Bot
Single-file, zero-maintenance design for Railway/Render deployment
"""

import os
import json
import logging
import yfinance as yf
import openai
import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import traceback
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Risk Gate 2.0 - Oracle's Advanced Safety System
import functools
import math
from collections import defaultdict
from enum import Enum

class MarketRegime(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"

class RiskGate:
    """Advanced risk management with sector limits, liquidity filters, and market regime detection"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Caches to reduce API calls
        self._sector_cache = {}
        self._dollar_volume_cache = {}
        self._regime_cache = None
        
    def filter_ai_orders(self, ai_orders, current_positions, current_equity):
        """Returns only orders that survive all safety checks"""
        safe_orders = []
        
        # Get market regime and adjust position limits
        regime = self._get_market_regime()
        regime_adj_max_position_pct = self._regime_adjusted_position_pct(regime)
        max_position_value = current_equity * regime_adj_max_position_pct
        
        self.logger.info(f"[RiskGate] Market regime = {regime.upper()} "
                        f"(max position {regime_adj_max_position_pct*100:.1f}% -> "
                        f"${max_position_value:,.0f})")
        
        # Calculate current sector exposure
        sector_exposure = self._calculate_sector_exposure(current_positions, current_equity)
        
        for order in ai_orders:
            try:
                current_price = self._get_current_price(order.ticker)
                order_value = order.qty * current_price
                
                # 1) Position size / regime cap
                if order_value > max_position_value:
                    self.logger.warning(f"❌ {order.ticker}: ${order_value:.0f} "
                                       f"exceeds max ${max_position_value:.0f} (regime cap)")
                    continue
                
                # 2) Duplicate positions
                if order.action == "BUY" and order.ticker in current_positions:
                    self.logger.warning(f"❌ {order.ticker}: already held")
                    continue
                
                # 3) Liquidity filter
                if order.action == "BUY" and not self._passes_liquidity_filter(order.ticker):
                    self.logger.warning(f"❌ {order.ticker}: fails liquidity screen")
                    continue
                
                # 4) Sector diversification
                sector = self._get_sector(order.ticker)
                projected_pct = (sector_exposure[sector] + order_value) / current_equity
                if projected_pct > self.config.sector_max_pct:
                    self.logger.warning(f"❌ {order.ticker}: "
                                       f"{sector} exposure {projected_pct*100:.1f}% "
                                       f"would breach {self.config.sector_max_pct*100:.0f}% max")
                    continue
                
                # Update running exposure for next orders
                sector_exposure[sector] += order_value
                
                safe_orders.append(order)
                self.logger.info(f"✅ {order.ticker}: order approved ({sector})")
                
            except Exception as e:
                self.logger.error(f"❌ {order.ticker}: risk check failed -> {e}")
                continue
        
        return safe_orders
    
    def _passes_liquidity_filter(self, ticker: str) -> bool:
        """Check average 20-day dollar volume and minimum price"""
        adv = self._get_avg_dollar_volume(ticker, days=20)
        price = self._get_current_price(ticker)
        return adv >= self.config.min_dollar_volume and price >= 0.50
    
    def _get_sector(self, ticker: str) -> str:
        """Get stock sector with caching"""
        if ticker in self._sector_cache:
            return self._sector_cache[ticker]
        
        try:
            info = yf.Ticker(ticker).info
            sector = info.get("sector", "Unknown")
        except:
            sector = "Unknown"
        
        self._sector_cache[ticker] = sector
        return sector
    
    def _get_avg_dollar_volume(self, ticker: str, days: int = 20) -> float:
        """Calculate average daily dollar volume"""
        if ticker in self._dollar_volume_cache:
            return self._dollar_volume_cache[ticker]
        
        try:
            hist = yf.Ticker(ticker).history(period=f"{days + 1}d")
            dv = (hist["Close"] * hist["Volume"]).tail(days).mean()
            dv = float(dv) if not math.isnan(dv) else 0.0
        except:
            dv = 0.0
        
        self._dollar_volume_cache[ticker] = dv
        return dv
    
    def _calculate_sector_exposure(self, positions, current_equity):
        """Calculate current sector exposure in dollars"""
        exposure = defaultdict(float)
        for ticker, pos in positions.items():
            value = self._get_current_price(ticker) * pos.shares
            sector = self._get_sector(ticker)
            exposure[sector] += value
        return exposure
    
    def _get_market_regime(self) -> MarketRegime:
        """Detect market regime using Russell 2000 moving averages"""
        # Cache for 6 hours
        if (self._regime_cache and 
            (datetime.now() - self._regime_cache[1]).seconds < 6 * 3600):
            return self._regime_cache[0]
        
        try:
            rut = yf.Ticker("^RUT").history(period="300d")["Close"]
            close = rut.iloc[-1]
            sma50 = rut.tail(50).mean()
            sma200 = rut.tail(200).mean()
            
            if close > sma50 > sma200:
                regime = MarketRegime.BULL
            elif close < sma200 and sma50 < sma200:
                regime = MarketRegime.BEAR
            else:
                regime = MarketRegime.SIDEWAYS
        except Exception as e:
            self.logger.warning(f"Failed to compute market regime: {e}")
            regime = MarketRegime.SIDEWAYS
        
        self._regime_cache = (regime, datetime.now())
        return regime
    
    def _regime_adjusted_position_pct(self, regime: MarketRegime) -> float:
        """Adjust position limits based on market regime"""
        if regime == MarketRegime.BEAR:
            return min(self.config.bear_max_position_pct, self.config.max_position_pct)
        if regime == MarketRegime.SIDEWAYS:
            return self.config.max_position_pct * 0.8
        return self.config.max_position_pct  # bull
    
    @functools.lru_cache(maxsize=256)
    def _get_current_price(self, ticker: str) -> float:
        """Get current stock price with caching"""
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            return float(hist["Close"].iloc[-1]) if not hist.empty else 0.0
        except:
            return 0.0

# ============================================================================
# Configuration from Environment Variables
# ============================================================================

@dataclass
class Config:
    # AI Settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    primary_model: str = os.getenv("AI_MODEL", "gpt-4")
    
    # Trading Settings
    starting_cash: float = float(os.getenv("STARTING_CASH", "1000"))
    max_position_pct: float = float(os.getenv("MAX_POSITION_PCT", "0.15"))  # 15% max
    stop_loss_pct: float = float(os.getenv("STOP_LOSS_PCT", "0.15"))  # 15% stop
    max_daily_loss_pct: float = float(os.getenv("MAX_DAILY_LOSS_PCT", "0.05"))  # 5% circuit breaker
    
    # Broker Settings
    alpaca_key: str = os.getenv("ALPACA_API_KEY", "")
    alpaca_secret: str = os.getenv("ALPACA_SECRET_KEY", "")
    paper_trading: bool = os.getenv("PAPER_TRADING", "true").lower() == "true"
    
    # Email Settings
    email_from: str = os.getenv("EMAIL_FROM", "")
    email_to: str = os.getenv("EMAIL_TO", "")
    email_password: str = os.getenv("EMAIL_PASSWORD", "")
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    
    # Storage
    state_file: str = os.getenv("STATE_FILE", "state.json")
    log_dir: str = os.getenv("LOG_DIR", "logs")
    
    # === NEW RISK PARAMETERS ===
    sector_max_pct: float = float(os.getenv("SECTOR_MAX_PCT", "0.40"))      # 40%
    min_dollar_volume: float = float(os.getenv("MIN_DOLLAR_VOLUME", "300000"))  # $300k ADV
    bear_max_position_pct: float = float(os.getenv("BEAR_MAX_POSITION_PCT", "0.07"))  # 7% cap in bear

# ============================================================================
# Data Models
# ============================================================================

class TradingOrder(BaseModel):
    action: str  # "BUY" or "SELL"
    ticker: str
    qty: int
    reasoning: str
    confidence: float = 0.5

class AIResponse(BaseModel):
    orders: List[TradingOrder]
    market_analysis: str = ""
    risk_assessment: str = ""

@dataclass
class Position:
    ticker: str
    shares: int
    avg_price: float
    stop_loss: float
    
@dataclass
class TradingState:
    cash: float
    positions: Dict[str, Position]
    total_equity: float
    daily_pnl: float
    last_update: str
    pending_orders: List[TradingOrder]
    
    def to_dict(self):
        return {
            'cash': self.cash,
            'positions': {k: asdict(v) for k, v in self.positions.items()},
            'total_equity': self.total_equity,
            'daily_pnl': self.daily_pnl,
            'last_update': self.last_update,
            'pending_orders': [order.dict() for order in self.pending_orders]
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        positions = {}
        for ticker, pos_data in data.get('positions', {}).items():
            positions[ticker] = Position(**pos_data)
        
        pending_orders = []
        for order_data in data.get('pending_orders', []):
            pending_orders.append(TradingOrder(**order_data))
        
        return cls(
            cash=data.get('cash', 0),
            positions=positions,
            total_equity=data.get('total_equity', 0),
            daily_pnl=data.get('daily_pnl', 0),
            last_update=data.get('last_update', ''),
            pending_orders=pending_orders
        )

# ============================================================================
# Main Trading Bot Class
# ============================================================================

class TradingBot:
    def __init__(self, config: Config):
        self.config = config
        self.setup_logging()
        self.setup_clients()
        
        # Initialize risk management
        self.risk_gate = RiskGate(config)
        
    def setup_logging(self):
        """Setup logging"""
        os.makedirs(self.config.log_dir, exist_ok=True)
        log_file = f"{self.config.log_dir}/{datetime.now().strftime('%Y-%m-%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_clients(self):
        """Initialize API clients"""
        # OpenAI client
        self.openai_client = openai.OpenAI(api_key=self.config.openai_api_key)
        
        # Alpaca client
        base_url = 'https://paper-api.alpaca.markets' if self.config.paper_trading else 'https://api.alpaca.markets'
        self.alpaca = tradeapi.REST(
            self.config.alpaca_key,
            self.config.alpaca_secret,
            base_url=base_url,
            api_version='v2'
        )
        
        self.logger.info(f"Initialized bot ({'paper' if self.config.paper_trading else 'live'} trading)")
    
    def load_state(self) -> TradingState:
        """Load trading state from JSON file"""
        try:
            if os.path.exists(self.config.state_file):
                with open(self.config.state_file, 'r') as f:
                    data = json.load(f)
                state = TradingState.from_dict(data)
                self.logger.info(f"Loaded state: ${state.total_equity:.2f} equity, {len(state.positions)} positions")
                return state
            else:
                # Initialize new state
                state = TradingState(
                    cash=self.config.starting_cash,
                    positions={},
                    total_equity=self.config.starting_cash,
                    daily_pnl=0.0,
                    last_update='',
                    pending_orders=[]
                )
                self.save_state(state)
                self.logger.info(f"Initialized new state with ${self.config.starting_cash}")
                return state
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
            raise
    
    def save_state(self, state: TradingState):
        """Save trading state to JSON file"""
        try:
            with open(self.config.state_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
            self.logger.debug("State saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            raise
    
    def get_market_data(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get current market data for tickers"""
        market_data = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                
                if len(hist) >= 2:
                    current_price = float(hist['Close'].iloc[-1])
                    prev_price = float(hist['Close'].iloc[-2])
                    volume = float(hist['Volume'].iloc[-1])
                    pct_change = ((current_price - prev_price) / prev_price) * 100
                    
                    market_data[ticker] = {
                        'price': current_price,
                        'prev_price': prev_price,
                        'pct_change': pct_change,
                        'volume': volume
                    }
                    
            except Exception as e:
                self.logger.warning(f"Failed to get data for {ticker}: {e}")
        
        return market_data
    
    def check_stop_losses(self, state: TradingState, market_data: Dict) -> List[TradingOrder]:
        """Check for stop loss triggers"""
        stop_orders = []
        
        for ticker, position in state.positions.items():
            if ticker in market_data:
                current_price = market_data[ticker]['price']
                if current_price <= position.stop_loss:
                    order = TradingOrder(
                        action="SELL",
                        ticker=ticker,
                        qty=position.shares,
                        reasoning=f"Stop loss triggered: ${current_price:.2f} <= ${position.stop_loss:.2f}",
                        confidence=1.0
                    )
                    stop_orders.append(order)
                    self.logger.warning(f"Stop loss triggered for {ticker}")
        
        return stop_orders
    
    def get_ai_decisions(self, state: TradingState, market_data: Dict) -> List[TradingOrder]:
        """Get trading decisions from AI"""
        try:
            prompt = self.build_trading_prompt(state, market_data)
            
            response = self.openai_client.chat.completions.create(
                model=self.config.primary_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content or ""
            self.logger.info(f"AI Response length: {len(content)} chars")
            
            # Parse AI response
            ai_response = self.parse_ai_response(content)
            return ai_response.orders
            
        except Exception as e:
            self.logger.error(f"AI decision failed: {e}")
            return []
    
    def build_trading_prompt(self, state: TradingState, market_data: Dict) -> str:
        """Build the AI trading prompt"""
        # Format current portfolio
        portfolio_lines = []
        for ticker, pos in state.positions.items():
            current_price = market_data.get(ticker, {}).get('price', 0)
            current_value = current_price * pos.shares
            pnl = (current_price - pos.avg_price) * pos.shares
            portfolio_lines.append(f"- {ticker}: {pos.shares} shares @ ${pos.avg_price:.2f} (now ${current_price:.2f}, P&L: ${pnl:+.2f})")
        
        # Format market data
        market_lines = []
        for ticker, data in market_data.items():
            market_lines.append(f"- {ticker}: ${data['price']:.2f} ({data['pct_change']:+.2f}%) Vol: {data['volume']:,.0f}")
        
        prompt = f"""You are managing a micro-cap stock portfolio. Analyze today's data and make trading decisions.

CURRENT PORTFOLIO (${state.total_equity:.2f} total equity):
{chr(10).join(portfolio_lines) if portfolio_lines else "- No positions"}
Cash: ${state.cash:.2f}

TODAY'S MARKET DATA:
{chr(10).join(market_lines)}

STRICT RULES (MUST FOLLOW):
- Only trade micro-cap stocks (market cap under $300M)
- MAXIMUM {self.config.max_position_pct*100:.0f}% position size per stock (HARD LIMIT)
- {self.config.stop_loss_pct*100:.0f}% stop losses are automatically set
- Maximum 40% in any single sector (biotech, tech, etc.)
- Target 60-90% cash deployment (holding some cash is OK)
- Focus on generating alpha vs Russell 2000

SUGGESTED MICRO-CAP RESEARCH AREAS:
- Small biotech/pharma companies with upcoming catalysts
- Technology companies with innovative products  
- Energy/mining companies with growth potential
- Small regional banks or specialty finance
- Consumer companies with niche products

EXAMPLE VALID MICRO-CAP TICKERS (verify current status):
ABEO, IINN, ACTU, BBAI, CDZI, FREQ, MVIS, RGTI, SNDX, VERB

Respond with trading decisions in JSON format:
{{
  "orders": [
    {{
      "action": "BUY",
      "ticker": "EXAMPLE",
      "qty": 10,
      "reasoning": "Strong momentum and volume",
      "confidence": 0.8
    }}
  ],
  "market_analysis": "Brief analysis of market conditions",
  "risk_assessment": "Current risk level assessment"
}}

Before finalizing orders, list any rule each order might breach (position size, sector limits, etc.).
Only submit orders that comply with ALL rules above.

IMPORTANT: You must verify each order is under 15% of portfolio value.
Example: For $1000 portfolio, max order size is $150 (not 50 shares of a $6 stock = $300)."""

        return prompt
    
    def parse_ai_response(self, content: str) -> AIResponse:
        """Parse AI response into structured format"""
        try:
            # Find JSON in response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = content[start_idx:end_idx]
            data = json.loads(json_str)
            
            return AIResponse(**data)
            
        except (json.JSONDecodeError, ValidationError) as e:
            self.logger.error(f"Failed to parse AI response: {e}")
            return AIResponse(orders=[])
    
    def execute_orders(self, orders: List[TradingOrder], state: TradingState) -> List[Dict]:
        """Execute trading orders"""
        results = []
        
        for order in orders:
            try:
                result = self.execute_single_order(order, state)
                results.append(result)
                
                # Update state based on successful execution
                if result['success']:
                    self.update_state_from_execution(state, order, result)
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Order execution failed: {e}")
                results.append({
                    'success': False,
                    'order': order.dict(),
                    'error': str(e)
                })
        
        return results
    
    def execute_single_order(self, order: TradingOrder, state: TradingState) -> Dict:
        """Execute a single trading order"""
        try:
            if order.action == "BUY":
                # Calculate order value
                current_price = self.get_current_price(order.ticker)
                order_value = order.qty * current_price
                
                if order_value > state.cash:
                    return {
                        'success': False,
                        'order': order.dict(),
                        'error': f"Insufficient cash: need ${order_value:.2f}, have ${state.cash:.2f}"
                    }
                
                # Place buy order
                alpaca_order = self.alpaca.submit_order(
                    symbol=order.ticker,
                    qty=order.qty,
                    side='buy',
                    type='market',
                    time_in_force='day'
                )
                
                self.logger.info(f"✅ BUY {order.ticker}: {order.qty} shares @ ~${current_price:.2f}")
                
                return {
                    'success': True,
                    'order': order.dict(),
                    'alpaca_order_id': alpaca_order.id,
                    'estimated_price': current_price
                }
                
            elif order.action == "SELL":
                if order.ticker not in state.positions:
                    return {
                        'success': False,
                        'order': order.dict(),
                        'error': f"No position in {order.ticker}"
                    }
                
                # Place sell order
                alpaca_order = self.alpaca.submit_order(
                    symbol=order.ticker,
                    qty=order.qty,
                    side='sell',
                    type='market',
                    time_in_force='day'
                )
                
                current_price = self.get_current_price(order.ticker)
                self.logger.info(f"✅ SELL {order.ticker}: {order.qty} shares @ ~${current_price:.2f}")
                
                return {
                    'success': True,
                    'order': order.dict(),
                    'alpaca_order_id': alpaca_order.id,
                    'estimated_price': current_price
                }
        
        except Exception as e:
            return {
                'success': False,
                'order': order.dict(),
                'error': str(e)
            }
    
    def update_state_from_execution(self, state: TradingState, order: TradingOrder, result: Dict):
        """Update state after successful order execution"""
        price = result.get('estimated_price', 0)
        
        if order.action == "BUY":
            # Add or update position
            if order.ticker in state.positions:
                pos = state.positions[order.ticker]
                total_shares = pos.shares + order.qty
                total_cost = (pos.shares * pos.avg_price) + (order.qty * price)
                new_avg_price = total_cost / total_shares
                
                state.positions[order.ticker] = Position(
                    ticker=order.ticker,
                    shares=total_shares,
                    avg_price=new_avg_price,
                    stop_loss=new_avg_price * (1 - self.config.stop_loss_pct)
                )
            else:
                state.positions[order.ticker] = Position(
                    ticker=order.ticker,
                    shares=order.qty,
                    avg_price=price,
                    stop_loss=price * (1 - self.config.stop_loss_pct)
                )
            
            state.cash -= order.qty * price
            
        elif order.action == "SELL":
            if order.ticker in state.positions:
                pos = state.positions[order.ticker]
                if order.qty >= pos.shares:
                    # Sell entire position
                    del state.positions[order.ticker]
                else:
                    # Partial sell
                    state.positions[order.ticker].shares -= order.qty
                
                state.cash += order.qty * price
    
    def get_current_price(self, ticker: str) -> float:
        """Get current price for ticker"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            return float(hist['Close'].iloc[-1]) if not hist.empty else 0
        except:
            return 0
    
    def calculate_performance(self, state: TradingState) -> Dict:
        """Calculate performance metrics"""
        total_return = (state.total_equity - self.config.starting_cash) / self.config.starting_cash
        
        # Get Russell 2000 benchmark
        try:
            rut = yf.Ticker("^RUT")
            rut_data = rut.history(period="1mo")
            rut_return = (rut_data['Close'].iloc[-1] - rut_data['Close'].iloc[0]) / rut_data['Close'].iloc[0]
        except:
            rut_return = 0
        
        return {
            'total_return_pct': total_return * 100,
            'benchmark_return_pct': rut_return * 100,
            'alpha_pct': (total_return - rut_return) * 100,
            'current_equity': state.total_equity,
            'num_positions': len(state.positions)
        }
    
    def send_email_report(self, state: TradingState, orders: List[TradingOrder], results: List[Dict], performance: Dict):
        """Send daily email report"""
        if not self.config.email_from or not self.config.email_to:
            self.logger.warning("Email not configured, skipping report")
            return
        
        try:
            # Build email content
            subject = f"Trading Bot Daily Report - ${state.total_equity:.2f} ({performance['total_return_pct']:+.2f}%)"
            
            body = f"""Daily Trading Report - {datetime.now().strftime('%Y-%m-%d')}

PORTFOLIO SUMMARY:
• Total Equity: ${state.total_equity:.2f}
• Cash: ${state.cash:.2f}
• Positions: {len(state.positions)}
• Total Return: {performance['total_return_pct']:+.2f}%
• vs Russell 2000: {performance['alpha_pct']:+.2f}% alpha

TODAY'S TRADES:
"""
            if orders:
                for order, result in zip(orders, results):
                    status = "✅" if result['success'] else "❌"
                    body += f"• {status} {order.action} {order.ticker}: {order.qty} shares - {order.reasoning}\n"
            else:
                body += "• No trades executed today\n"
            
            body += f"\nCURRENT POSITIONS:\n"
            for ticker, pos in state.positions.items():
                current_price = self.get_current_price(ticker)
                pnl = (current_price - pos.avg_price) * pos.shares
                body += f"• {ticker}: {pos.shares} shares @ ${pos.avg_price:.2f} (P&L: ${pnl:+.2f})\n"
            
            # Send email
            msg = MIMEMultipart()
            msg['From'] = self.config.email_from
            msg['To'] = self.config.email_to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.email_from, self.config.email_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Email report sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
    
    def run_daily_cycle(self):
        """Run the complete daily trading cycle"""
        try:
            self.logger.info("=== Starting Daily Trading Cycle ===")
            
            # Load current state
            state = self.load_state()
            
            # Get market data
            all_tickers = list(state.positions.keys()) + ["^RUT", "IWO", "XBI"]
            market_data = self.get_market_data(all_tickers)
            
            # Update portfolio values
            total_value = state.cash
            for ticker, pos in state.positions.items():
                if ticker in market_data:
                    total_value += market_data[ticker]['price'] * pos.shares
            state.total_equity = total_value
            
            # Check stop losses
            stop_orders = self.check_stop_losses(state, market_data)
            
            # Get AI decisions
            ai_orders = self.get_ai_decisions(state, market_data)
            
            # Combine all orders
            all_orders = stop_orders + ai_orders
            
            # Filter orders through risk gate
            if all_orders:
                safe_orders = self.risk_gate.filter_ai_orders(all_orders, state.positions, state.total_equity)
                if safe_orders:
                    results = self.execute_orders(safe_orders, state)
                    self.logger.info(f"Executed {len(safe_orders)}/{len(all_orders)} orders after risk filtering")
                else:
                    results = []
                    self.logger.warning("All orders filtered out by risk gate")
            else:
                results = []
                self.logger.info("No trading decisions made")
            
            # Update timestamp
            state.last_update = datetime.now().isoformat()
            
            # Save state
            self.save_state(state)
            
            # Calculate performance
            performance = self.calculate_performance(state)
            
            # Send report
            self.send_email_report(state, all_orders, results, performance)
            
            self.logger.info(f"=== Cycle Complete: ${state.total_equity:.2f} equity ===")
            
        except Exception as e:
            self.logger.error(f"Daily cycle failed: {e}")
            self.logger.error(traceback.format_exc())
            
            # Send error alert
            try:
                self.send_error_alert(str(e))
            except:
                pass
            
            raise
    
    def send_error_alert(self, error_msg: str):
        """Send error alert email"""
        if not self.config.email_from or not self.config.email_to:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.email_from
            msg['To'] = self.config.email_to
            msg['Subject'] = "🚨 Trading Bot Error Alert"
            
            body = f"""Trading Bot Error - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Error: {error_msg}

The trading bot encountered an error and may need attention.
Check the logs for more details.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.email_from, self.config.email_password)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"Failed to send error alert: {e}")

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    try:
        config = Config()
        
        # Validate required config
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
        if not config.alpaca_key or not config.alpaca_secret:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables required")
        
        bot = TradingBot(config)
        bot.run_daily_cycle()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
