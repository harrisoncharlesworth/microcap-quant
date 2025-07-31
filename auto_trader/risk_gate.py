"""
Risk Gate - Code-level validation layer that prevents bad trades
"""

import yfinance as yf
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta

@dataclass
class OrderTicket:
    symbol: str
    side: str         # 'buy' / 'sell'
    qty: int
    limit_price: float
    reason: str = ""
    confidence: float = 0.5

class RiskViolation(Exception):
    """Exception raised when trade violates risk rules"""
    pass

class RiskGate:
    """Code-level validation that prevents bad trades regardless of AI decisions"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Risk limits
        self.max_position_pct = config.max_position_pct  # 0.15 = 15%
        self.max_sector_pct = 0.25  # 25% max per sector
        self.min_liquidity = 500_000  # $500k minimum daily volume
        self.max_spread_pct = 0.03  # 3% max bid-ask spread
        
    def check_position_size(self, ticket: OrderTicket, current_equity: float):
        """Ensure position doesn't exceed maximum size limit"""
        order_value = ticket.qty * ticket.limit_price
        max_allowed = current_equity * self.max_position_pct
        
        if order_value > max_allowed:
            raise RiskViolation(
                f"Position size ${order_value:.0f} exceeds {self.max_position_pct*100:.0f}% "
                f"limit of ${max_allowed:.0f}"
            )
    
    def check_duplicate_position(self, ticket: OrderTicket, current_positions: Dict):
        """Prevent buying more of same stock if already long"""
        if ticket.side == 'buy' and ticket.symbol in current_positions:
            current_shares = current_positions[ticket.symbol].get('shares', 0)
            if current_shares > 0:
                raise RiskViolation(f"Already long {current_shares} shares of {ticket.symbol}")
    
    def check_liquidity(self, symbol: str) -> bool:
        """Check if stock has sufficient liquidity for safe trading"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="30d")
            
            if hist.empty or len(hist) < 20:
                raise RiskViolation(f"{symbol}: Insufficient price history")
            
            # Calculate average daily dollar volume
            avg_volume = hist['Volume'].mean()
            avg_price = hist['Close'].mean()
            daily_dollar_volume = avg_volume * avg_price
            
            if daily_dollar_volume < self.min_liquidity:
                raise RiskViolation(
                    f"{symbol}: Daily volume ${daily_dollar_volume:,.0f} below "
                    f"${self.min_liquidity:,} minimum"
                )
            
            # Check latest bid-ask spread (approximated)
            latest_price = hist['Close'].iloc[-1]
            high_low_spread = (hist['High'].iloc[-1] - hist['Low'].iloc[-1]) / latest_price
            
            if high_low_spread > self.max_spread_pct:
                self.logger.warning(f"{symbol}: Wide spread {high_low_spread*100:.1f}%")
            
            return True
            
        except Exception as e:
            raise RiskViolation(f"{symbol}: Liquidity check failed - {e}")
    
    def get_sector(self, symbol: str) -> str:
        """Get stock sector (simplified - in production use proper data feed)"""
        # Simplified sector mapping - in production use GICS data
        biotech_tickers = ['ABEO', 'IINN', 'CDZI', 'SNDX', 'FREQ']
        tech_tickers = ['BBAI', 'MVIS', 'VERB', 'RGTI']
        
        if symbol in biotech_tickers:
            return 'Healthcare'
        elif symbol in tech_tickers:
            return 'Technology'
        else:
            return 'Other'
    
    def check_sector_exposure(self, ticket: OrderTicket, current_positions: Dict, 
                            current_equity: float):
        """Ensure sector diversification limits"""
        sector = self.get_sector(ticket.symbol)
        
        # Calculate current sector exposure
        sector_value = 0
        for symbol, position in current_positions.items():
            if self.get_sector(symbol) == sector:
                shares = position.get('shares', 0)
                price = self.get_current_price(symbol)
                sector_value += shares * price
        
        # Add proposed order value
        order_value = ticket.qty * ticket.limit_price
        total_sector_value = sector_value + order_value
        
        max_allowed = current_equity * self.max_sector_pct
        
        if total_sector_value > max_allowed:
            raise RiskViolation(
                f"Sector exposure {sector}: ${total_sector_value:.0f} exceeds "
                f"{self.max_sector_pct*100:.0f}% limit of ${max_allowed:.0f}"
            )
    
    def get_current_price(self, symbol: str) -> float:
        """Get current stock price"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            return float(hist['Close'].iloc[-1]) if not hist.empty else 0
        except:
            return 0
    
    def check_market_conditions(self) -> str:
        """Simple market regime detection"""
        try:
            spy = yf.Ticker("SPY")
            hist = spy.history(period="200d")
            
            if len(hist) < 200:
                return "UNKNOWN"
            
            sma50 = hist['Close'][-50:].mean()
            sma200 = hist['Close'][-200:].mean()
            current_vol = hist['Close'][-20:].pct_change().std() * (252**0.5)
            
            if sma50 > sma200 and current_vol < 0.20:
                return "BULL"
            elif sma50 < sma200:
                return "BEAR"
            else:
                return "SIDEWAYS"
                
        except Exception as e:
            self.logger.warning(f"Market condition check failed: {e}")
            return "UNKNOWN"
    
    def validate_order(self, ticket: OrderTicket, current_positions: Dict, 
                      current_equity: float) -> bool:
        """Master validation function - returns True if order is safe"""
        try:
            self.logger.info(f"Validating order: {ticket.side} {ticket.qty} {ticket.symbol}")
            
            # Core safety checks
            self.check_position_size(ticket, current_equity)
            self.check_duplicate_position(ticket, current_positions)
            self.check_liquidity(ticket.symbol)
            self.check_sector_exposure(ticket, current_positions, current_equity)
            
            # Market condition check
            market_regime = self.check_market_conditions()
            if market_regime == "BEAR" and ticket.side == 'buy':
                self.logger.warning(f"Bear market detected - reducing risk")
                # In bear market, only allow smaller positions
                if ticket.qty * ticket.limit_price > current_equity * 0.05:  # 5% max in bear
                    raise RiskViolation("Bear market: reducing position size limit to 5%")
            
            self.logger.info(f"✅ Order validation passed for {ticket.symbol}")
            return True
            
        except RiskViolation as e:
            self.logger.error(f"❌ Order rejected: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Validation error: {e}")
            return False
    
    def filter_ai_orders(self, ai_orders: List, current_positions: Dict, 
                        current_equity: float) -> List:
        """Filter AI-generated orders through risk checks"""
        safe_orders = []
        
        for order_data in ai_orders:
            ticket = OrderTicket(
                symbol=order_data.ticker,
                side=order_data.action.lower(),
                qty=order_data.qty,
                limit_price=self.get_current_price(order_data.ticker),
                reason=order_data.reasoning,
                confidence=order_data.confidence
            )
            
            if self.validate_order(ticket, current_positions, current_equity):
                safe_orders.append(order_data)
            else:
                self.logger.warning(f"Filtered out unsafe order: {order_data.ticker}")
        
        return safe_orders
