"""
Broker Interface - Handles automated trade execution
"""
import alpaca_trade_api as tradeapi
import yfinance as yf
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .config import TradingConfig
from .ai_decision_engine import TradingDecision

@dataclass
class OrderResult:
    success: bool
    order_id: Optional[str] = None
    error_message: Optional[str] = None
    filled_price: Optional[float] = None
    filled_qty: Optional[int] = None

class BrokerInterface:
    def __init__(self, config: TradingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Alpaca API with proper credential handling
        import os
        
        # Resolve credentials from config or environment variables
        api_key = (config.alpaca_api_key 
                  or os.getenv("ALPACA_API_KEY") 
                  or os.getenv("APCA_API_KEY_ID"))
        api_secret = (config.alpaca_secret_key 
                     or os.getenv("ALPACA_SECRET_KEY") 
                     or os.getenv("APCA_API_SECRET_KEY"))
        
        if not api_key or not api_secret:
            raise ValueError("Alpaca API credentials not found in config or environment variables")
        
        base_url = 'https://paper-api.alpaca.markets' if config.paper_trading else 'https://api.alpaca.markets'
        self.api = tradeapi.REST(
            api_key,
            api_secret,
            base_url=base_url,
            api_version='v2'
        )
        
        self.logger.info(f"Initialized broker interface ({'paper' if config.paper_trading else 'live'} trading)")
    
    def execute_decisions(self, decisions: List[TradingDecision], current_cash: float, 
                         current_positions: Dict) -> List[OrderResult]:
        """Execute a list of trading decisions"""
        results = []
        
        for decision in decisions:
            if decision.action == "BUY":
                result = self._execute_buy(decision, current_cash)
            elif decision.action == "SELL":
                result = self._execute_sell(decision, current_positions)
            else:  # HOLD
                result = OrderResult(success=True)
            
            results.append(result)
            
            # Update cash and positions for next iteration
            if result.success and decision.action == "BUY" and result.filled_price:
                current_cash -= result.filled_price * result.filled_qty
            elif result.success and decision.action == "SELL" and result.filled_price:
                current_cash += result.filled_price * result.filled_qty
        
        return results
    
    def _execute_buy(self, decision: TradingDecision, available_cash: float) -> OrderResult:
        """Execute a buy order"""
        try:
            # Get current price
            current_price = self._get_current_price(decision.ticker)
            if not current_price:
                return OrderResult(success=False, error_message="Could not get current price")
            
            # Calculate position size
            if decision.position_size:
                # Use specified position size (% of portfolio)
                total_equity = available_cash  # Simplified - should include current positions value
                dollar_amount = total_equity * decision.position_size
            else:
                # Default to maximum allowed position size
                dollar_amount = available_cash * self.config.max_position_size
            
            # Calculate shares to buy
            shares = int(dollar_amount / current_price)
            
            if shares == 0:
                return OrderResult(success=False, error_message="Insufficient funds for even 1 share")
            
            # Check if we have enough cash
            total_cost = shares * current_price
            if total_cost > available_cash:
                shares = int(available_cash / current_price)
                total_cost = shares * current_price
            
            # Place market order
            order = self.api.submit_order(
                symbol=decision.ticker,
                qty=shares,
                side='buy',
                type='market',
                time_in_force='day'
            )
            
            self.logger.info(f"Placed buy order: {shares} shares of {decision.ticker} @ ${current_price:.2f}")
            
            return OrderResult(
                success=True,
                order_id=order.id,
                filled_price=current_price,
                filled_qty=shares
            )
            
        except Exception as e:
            self.logger.error(f"Buy order failed for {decision.ticker}: {e}")
            return OrderResult(success=False, error_message=str(e))
    
    def _execute_sell(self, decision: TradingDecision, current_positions: Dict) -> OrderResult:
        """Execute a sell order"""
        try:
            ticker = decision.ticker
            
            if ticker not in current_positions:
                return OrderResult(success=False, error_message=f"No position in {ticker}")
            
            position = current_positions[ticker]
            shares = position.get('shares', 0)
            
            if shares <= 0:
                return OrderResult(success=False, error_message=f"No shares to sell for {ticker}")
            
            # Get current price
            current_price = self._get_current_price(ticker)
            if not current_price:
                return OrderResult(success=False, error_message="Could not get current price")
            
            # Place market order to sell all shares
            order = self.api.submit_order(
                symbol=ticker,
                qty=shares,
                side='sell',
                type='market',
                time_in_force='day'
            )
            
            self.logger.info(f"Placed sell order: {shares} shares of {ticker} @ ${current_price:.2f}")
            
            return OrderResult(
                success=True,
                order_id=order.id,
                filled_price=current_price,
                filled_qty=shares
            )
            
        except Exception as e:
            self.logger.error(f"Sell order failed for {decision.ticker}: {e}")
            return OrderResult(success=False, error_message=str(e))
    
    def check_stop_losses(self, current_positions: Dict) -> List[TradingDecision]:
        """Check all positions for stop loss triggers"""
        stop_loss_decisions = []
        
        for ticker, position in current_positions.items():
            if ticker == "TOTAL":  # Skip total row
                continue
                
            current_price = self._get_current_price(ticker)
            buy_price = position.get('buy_price', position.get('avg_entry_price', position.get('avg_price', 0)))
            stop_loss = position.get('stop_loss')
            
            # Compute stop loss if missing (15% below buy price)
            if stop_loss is None and buy_price > 0:
                stop_loss = buy_price * 0.85  # 15% stop loss
            
            if current_price and stop_loss and current_price <= stop_loss:
                decision = TradingDecision(
                    action="SELL",
                    ticker=ticker,
                    confidence=1.0,
                    reasoning=f"Stop loss triggered: ${current_price:.2f} <= ${stop_loss:.2f}"
                )
                stop_loss_decisions.append(decision)
                self.logger.warning(f"Stop loss triggered for {ticker}")
        
        return stop_loss_decisions
    
    def get_account_info(self) -> Dict:
        """Get current account information"""
        try:
            account = self.api.get_account()
            positions = self.api.list_positions()
            
            return {
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'total_equity': float(account.equity),
                'positions': {pos.symbol: {
                    'shares': int(pos.qty),
                    'market_value': float(pos.market_value),
                    'avg_entry_price': float(pos.avg_entry_price)
                } for pos in positions}
            }
        except Exception as e:
            self.logger.error(f"Failed to get account info: {e}")
            return {}
    
    def _get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price for a ticker"""
        try:
            # Try Alpaca first
            try:
                latest_trade = self.api.get_latest_trade(ticker)
                return float(latest_trade.price)
            except:
                pass
            
            # Fallback to yfinance
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get price for {ticker}: {e}")
            return None
    
    def validate_ticker(self, ticker: str) -> bool:
        """Validate if ticker is tradeable"""
        try:
            asset = self.api.get_asset(ticker)
            return asset.tradable and asset.status == 'active'
        except:
            return False
