"""
Main Automated Trading System
"""
import pandas as pd
import yfinance as yf
import logging
import json
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List
import sys
import os

# Add parent directory to path to import existing modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import TradingConfig, BENCHMARK_TICKERS, DEEP_RESEARCH_DAYS
from ai_decision_engine import AIDecisionEngine, TradingDecision
from broker_interface import BrokerInterface, OrderResult
from notification_system import NotificationSystem

class AutomatedTrader:
    def __init__(self, config: TradingConfig):
        self.config = config
        self.setup_logging()
        
        # Initialize components
        self.ai_engine = AIDecisionEngine(config)
        self.broker = BrokerInterface(config)
        self.notifications = NotificationSystem(config)
        
        self.logger.info("Automated Trader initialized")
        
        # Load existing portfolio
        self.portfolio_file = os.path.join(config.data_dir, config.portfolio_file)
        self.trade_log_file = os.path.join(config.data_dir, config.trade_log_file)
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('auto_trader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_daily_cycle(self):
        """Run the complete daily trading cycle"""
        try:
            self.logger.info("=== Starting Daily Trading Cycle ===")
            
            # 1. Get current portfolio and market data
            portfolio_data = self.load_current_portfolio()
            market_data = self.get_market_data(portfolio_data)
            
            # 2. Check for stop losses first
            stop_loss_decisions = self.broker.check_stop_losses(portfolio_data['positions'])
            if stop_loss_decisions:
                self.logger.warning(f"Executing {len(stop_loss_decisions)} stop loss orders")
                self.execute_and_log_trades(stop_loss_decisions, portfolio_data)
                # Reload portfolio after stop losses
                portfolio_data = self.load_current_portfolio()
            
            # 3. Get AI decisions
            is_research_day = datetime.now().strftime('%A').lower() in DEEP_RESEARCH_DAYS
            
            if is_research_day:
                self.logger.info("Running weekly deep research")
                decisions = self.ai_engine.make_weekly_research(portfolio_data)
            else:
                self.logger.info("Running daily analysis")
                decisions = self.ai_engine.make_daily_decisions(portfolio_data, market_data)
            
            # 4. Execute trades
            if decisions:
                self.execute_and_log_trades(decisions, portfolio_data)
            else:
                self.logger.info("No trading decisions made")
            
            # 5. Update portfolio records
            self.update_portfolio_records()
            
            # 6. Generate performance report
            performance = self.calculate_performance()
            
            # 7. Send notifications
            self.notifications.send_daily_report(decisions, performance)
            
            self.logger.info("=== Daily Trading Cycle Complete ===")
            
        except Exception as e:
            self.logger.error(f"Daily cycle failed: {e}")
            self.notifications.send_error_alert(str(e))
    
    def execute_and_log_trades(self, decisions: List[TradingDecision], portfolio_data: Dict):
        """Execute trades and log results"""
        current_cash = portfolio_data.get('cash', 0)
        current_positions = portfolio_data.get('positions', {})
        
        # Execute trades
        results = self.broker.execute_decisions(decisions, current_cash, current_positions)
        
        # Log each trade
        for decision, result in zip(decisions, results):
            self.log_trade(decision, result)
            
            if result.success:
                self.logger.info(f"✅ {decision.action} {decision.ticker}: {result.filled_qty} shares @ ${result.filled_price:.2f}")
            else:
                self.logger.error(f"❌ {decision.action} {decision.ticker} failed: {result.error_message}")
    
    def load_current_portfolio(self) -> Dict:
        """Load current portfolio from CSV and broker"""
        try:
            # Get live account info from broker
            account_info = self.broker.get_account_info()
            
            if account_info:
                # Use live broker data
                return {
                    'cash': account_info['cash'],
                    'total_equity': account_info['total_equity'],
                    'positions': account_info['positions']
                }
            else:
                # Fallback to CSV data (existing system)
                if os.path.exists(self.portfolio_file):
                    df = pd.read_csv(self.portfolio_file)
                    latest = df[df['Date'] == df['Date'].max()]
                    
                    positions = {}
                    total_row = latest[latest['Ticker'] == 'TOTAL'].iloc[0]
                    
                    for _, row in latest[latest['Ticker'] != 'TOTAL'].iterrows():
                        positions[row['Ticker']] = {
                            'shares': int(row['Shares']),
                            'buy_price': float(row['Cost Basis']),
                            'stop_loss': float(row['Stop Loss'])
                        }
                    
                    return {
                        'cash': float(total_row['Cash Balance']),
                        'total_equity': float(total_row['Total Equity']),
                        'positions': positions
                    }
                else:
                    # Initialize with starting cash
                    return {
                        'cash': self.config.starting_cash,
                        'total_equity': self.config.starting_cash,
                        'positions': {}
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to load portfolio: {e}")
            return {
                'cash': self.config.starting_cash,
                'total_equity': self.config.starting_cash,
                'positions': {}
            }
    
    def get_market_data(self, portfolio_data: Dict) -> Dict:
        """Get current market data for portfolio and benchmarks"""
        tickers = list(portfolio_data['positions'].keys()) + BENCHMARK_TICKERS
        market_data = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                
                if len(hist) >= 2:
                    current_price = float(hist['Close'].iloc[-1])
                    prev_price = float(hist['Close'].iloc[-2])
                    volume = float(hist['Volume'].iloc[-1])
                    percent_change = ((current_price - prev_price) / prev_price) * 100
                    
                    market_data[ticker] = {
                        'price': current_price,
                        'percent_change': percent_change,
                        'volume': volume
                    }
                    
            except Exception as e:
                self.logger.warning(f"Failed to get data for {ticker}: {e}")
        
        return market_data
    
    def log_trade(self, decision: TradingDecision, result: OrderResult):
        """Log trade to CSV file"""
        if not result.success:
            return
            
        trade_data = {
            'Date': datetime.now().strftime('%Y-%m-%d'),
            'Ticker': decision.ticker,
            'Action': decision.action,
            'Shares': result.filled_qty or 0,
            'Price': result.filled_price or 0,
            'Confidence': decision.confidence,
            'Reasoning': decision.reasoning,
            'Order_ID': result.order_id or '',
            'AI_Model': self.config.primary_model
        }
        
        # Append to trade log
        df = pd.DataFrame([trade_data])
        
        if os.path.exists(self.trade_log_file):
            existing = pd.read_csv(self.trade_log_file)
            df = pd.concat([existing, df], ignore_index=True)
        
        df.to_csv(self.trade_log_file, index=False)
    
    def update_portfolio_records(self):
        """Update portfolio CSV with current positions"""
        try:
            account_info = self.broker.get_account_info()
            if not account_info:
                return
            
            today = datetime.now().strftime('%Y-%m-%d')
            records = []
            
            # Add position rows
            for ticker, position in account_info['positions'].items():
                current_price = self._get_current_price(ticker)
                if current_price:
                    shares = position['shares']
                    cost_basis = position['avg_entry_price']
                    total_value = current_price * shares
                    pnl = (current_price - cost_basis) * shares
                    
                    records.append({
                        'Date': today,
                        'Ticker': ticker,
                        'Shares': shares,
                        'Cost Basis': cost_basis,
                        'Stop Loss': cost_basis * (1 - self.config.stop_loss_pct),
                        'Current Price': current_price,
                        'Total Value': total_value,
                        'PnL': pnl,
                        'Action': 'HOLD',
                        'Cash Balance': '',
                        'Total Equity': ''
                    })
            
            # Add total row
            records.append({
                'Date': today,
                'Ticker': 'TOTAL',
                'Shares': '',
                'Cost Basis': '',
                'Stop Loss': '',
                'Current Price': '',
                'Total Value': sum(r['Total Value'] for r in records),
                'PnL': sum(r['PnL'] for r in records),
                'Action': '',
                'Cash Balance': account_info['cash'],
                'Total Equity': account_info['total_equity']
            })
            
            # Update CSV
            df = pd.DataFrame(records)
            
            if os.path.exists(self.portfolio_file):
                existing = pd.read_csv(self.portfolio_file)
                # Remove today's records if they exist
                existing = existing[existing['Date'] != today]
                df = pd.concat([existing, df], ignore_index=True)
            
            df.to_csv(self.portfolio_file, index=False)
            self.logger.info("Portfolio records updated")
            
        except Exception as e:
            self.logger.error(f"Failed to update portfolio records: {e}")
    
    def calculate_performance(self) -> Dict:
        """Calculate current performance metrics"""
        try:
            if not os.path.exists(self.portfolio_file):
                return {}
            
            df = pd.read_csv(self.portfolio_file)
            totals = df[df['Ticker'] == 'TOTAL'].copy()
            
            if len(totals) < 2:
                return {}
            
            # Calculate returns
            current_equity = float(totals['Total Equity'].iloc[-1])
            initial_equity = self.config.starting_cash
            
            total_return = (current_equity - initial_equity) / initial_equity
            
            # Get benchmark data (Russell 2000)
            try:
                rut = yf.Ticker("^RUT")
                rut_data = rut.history(period="6mo")
                rut_return = (rut_data['Close'].iloc[-1] - rut_data['Close'].iloc[0]) / rut_data['Close'].iloc[0]
            except:
                rut_return = 0
            
            return {
                'total_return': total_return,
                'current_equity': current_equity,
                'benchmark_return': rut_return,
                'alpha': total_return - rut_return,
                'num_positions': len([t for t in df['Ticker'].iloc[-10:] if t != 'TOTAL'])
            }
            
        except Exception as e:
            self.logger.error(f"Performance calculation failed: {e}")
            return {}
    
    def _get_current_price(self, ticker: str) -> float:
        """Get current price for ticker"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            return float(hist['Close'].iloc[-1]) if not hist.empty else 0
        except:
            return 0
    
    def start_automated_trading(self):
        """Start the automated trading schedule"""
        self.logger.info("Starting automated trading system...")
        
        # Schedule daily trading
        schedule.every().day.at(self.config.trading_time).do(self.run_daily_cycle)
        
        # Initial health check
        self.notifications.send_startup_notification()
        
        self.logger.info(f"Scheduled daily trading at {self.config.trading_time} {self.config.timezone}")
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point"""
    config = TradingConfig()
    trader = AutomatedTrader(config)
    
    if len(sys.argv) > 1 and sys.argv[1] == "run-once":
        # Run once for testing
        trader.run_daily_cycle()
    else:
        # Start automated schedule
        trader.start_automated_trading()

if __name__ == "__main__":
    main()
