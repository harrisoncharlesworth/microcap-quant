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
import pytz
from typing import Dict, List
import sys
import os
from concurrent.futures import ThreadPoolExecutor, Future

# Add parent directory to path to import existing modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import sys
import os
sys.path.append(os.path.dirname(__file__))
from .config import TradingConfig, BENCHMARK_TICKERS, DEEP_RESEARCH_DAYS
from .ai_decision_engine import AIDecisionEngine, TradingDecision
from .broker_interface import BrokerInterface, OrderResult
from .notification_system import NotificationSystem

class AutomatedTrader:
    def __init__(self, config: TradingConfig):
        self.config = config
        self.setup_logging()
        
        # Initialize components
        self.ai_engine = AIDecisionEngine(config)
        self.broker = BrokerInterface(config)
        self.notifications = NotificationSystem(config)
        
        # Initialize thread pool for non-blocking job execution
        self.thread_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="trader")
        self.active_jobs = {}  # Track running jobs
        
        self.logger.info("Automated Trader initialized with ThreadPoolExecutor")
        
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
    
    def run_opening_cycle(self):
        """09:30 EST – heavy research + optional trades"""
        try:
            self.logger.info("=== Starting Market-Open Research Cycle ===")
            portfolio_data = self.load_current_portfolio()

            # 1. Deep research with alternate model
            decisions = self.ai_engine.make_deep_research(portfolio_data)

            # 2. Execute (same safety gates as daily cycle)
            if decisions:
                self.execute_and_log_trades(decisions, portfolio_data)
            else:
                self.logger.info("No research-driven trades generated")

            # 3. Update and report (reuse existing helpers)
            self.update_portfolio_records()
            performance = self.calculate_performance()
            self.notifications.send_custom_report(
                title="Market-Open Research Report",
                decisions=decisions,
                performance=performance
            )

            self.logger.info("=== Market-Open Research Cycle Complete ===")
        except Exception as e:
            self.logger.error(f"Market-open cycle failed: {e}")
            self.notifications.send_error_alert(str(e))

    def run_intraday_news_check(self):
        """11:00 AM EST – quick news refresh (Oracle's recommendation)"""
        try:
            self.logger.info("=== Starting Intraday News Check ===")
            
            # Quick news-based analysis without heavy trading
            portfolio_data = self.load_current_portfolio()
            
            # Use primary model for quick news analysis
            prompt = f"""Quick intraday news analysis for current portfolio:
            
{self._format_portfolio(portfolio_data)}

Check for breaking news, earnings updates, or major market events that might affect current positions.
Provide brief confidence adjustments and any urgent alerts needed.

Respond with JSON format for any urgent actions only:
{{"decisions": [], "alerts": []}}"""
            
            response = self.ai_engine._call_ai_model(prompt, self.config.primary_model, max_tokens=500)
            
            try:
                import json
                data = json.loads(response)
                alerts = data.get("alerts", [])
                
                if alerts:
                    self.logger.warning(f"Intraday alerts: {alerts}")
                    self.notifications.send_daily_report([], {})
                    self.logger.warning(f"Sent intraday alerts: {', '.join(alerts)}")
                else:
                    self.logger.info("No urgent intraday alerts")
                    
            except:
                self.logger.info("News check completed - no structured alerts")
            
            self.logger.info("=== Intraday News Check Complete ===")
            
        except Exception as e:
            self.logger.error(f"Intraday news check failed: {e}")

    def _format_portfolio(self, portfolio_data: Dict) -> str:
        """Helper method to format portfolio for prompts"""
        if not portfolio_data.get('positions'):
            return f"Cash: ${portfolio_data.get('cash', 0):.2f}, Total Equity: ${portfolio_data.get('total_equity', 0):.2f}"
        
        lines = [f"Cash: ${portfolio_data.get('cash', 0):.2f}"]
        for ticker, pos in portfolio_data['positions'].items():
            # Handle missing buy_price key with safe fallback
            shares = pos.get('shares', 0)
            buy_price = pos.get('buy_price', pos.get('avg_entry_price', pos.get('avg_price', 0)))
            lines.append(f"{ticker}: {shares} shares @ ${buy_price:.2f}")
        lines.append(f"Total Equity: ${portfolio_data.get('total_equity', 0):.2f}")
        return "\n".join(lines)

    def _safe_job_wrapper(self, job_name: str, job_func):
        """Wrapper for threaded jobs with error handling and logging"""
        try:
            self.logger.info(f"Starting threaded job: {job_name}")
            job_func()
            self.logger.info(f"Completed threaded job: {job_name}")
        except Exception as e:
            self.logger.error(f"Threaded job {job_name} failed: {e}")
            self.notifications.send_error_alert(f"Job {job_name} failed: {str(e)}")
        finally:
            # Remove from active jobs tracking
            if job_name in self.active_jobs:
                del self.active_jobs[job_name]

    def _submit_job(self, job_name: str, job_func):
        """Submit job to thread pool if not already running"""
        if job_name in self.active_jobs:
            self.logger.warning(f"Job {job_name} already running, skipping...")
            return
        
        self.logger.info(f"Submitting job to thread pool: {job_name}")
        future = self.thread_pool.submit(self._safe_job_wrapper, job_name, job_func)
        self.active_jobs[job_name] = future

    def convert_et_to_utc(self, et_time_str: str) -> str:
        """Convert Eastern Time to UTC for scheduling, ensuring future time"""
        et_tz = pytz.timezone('US/Eastern')
        utc_tz = pytz.timezone('UTC')
        
        # Get current time in ET
        current_et = datetime.now(et_tz)
        
        # Create today's date with desired ET time
        et_time = datetime.strptime(et_time_str, "%H:%M").time()
        et_datetime = datetime.combine(current_et.date(), et_time)
        et_datetime = et_tz.localize(et_datetime)
        
        # If the time has already passed today, schedule for tomorrow
        if et_datetime <= current_et:
            et_datetime = et_datetime + timedelta(days=1)
            self.logger.info(f"Time {et_time_str} ET has passed today, scheduling for tomorrow")
        
        # Convert to UTC
        utc_datetime = et_datetime.astimezone(utc_tz)
        return utc_datetime.strftime("%H:%M")

    def start_automated_trading(self):
        """Start the automated trading schedule"""
        self.logger.info("Starting automated trading system...")
        
        # Convert ET times to UTC for container scheduling
        trading_time_utc = self.convert_et_to_utc(self.config.trading_time)
        pre_market_time_utc = self.convert_et_to_utc(self.config.pre_market_research_time)
        intraday_time_utc = self.convert_et_to_utc(self.config.intraday_news_time)
        
        # Schedule daily trading at market close (using thread pool)
        schedule.every().day.at(trading_time_utc).do(self._submit_job, "daily_cycle", self.run_daily_cycle)
        
        # Schedule deep research pre-market (Oracle's recommendation)
        schedule.every().day.at(pre_market_time_utc).do(self._submit_job, "opening_cycle", self.run_opening_cycle)
        
        # Schedule optional intraday news refresh
        schedule.every().day.at(intraday_time_utc).do(self._submit_job, "intraday_news", self.run_intraday_news_check)
        
        # Initial health check
        self.notifications.send_startup_notification()
        
        self.logger.info(f"Scheduled daily trading at {self.config.trading_time} ET ({trading_time_utc} UTC)")
        self.logger.info(f"Scheduled pre-market research at {self.config.pre_market_research_time} ET ({pre_market_time_utc} UTC)")
        self.logger.info(f"Scheduled intraday news check at {self.config.intraday_news_time} ET ({intraday_time_utc} UTC)")
        
        # Keep running with thread monitoring and crash protection
        heartbeat_counter = 0
        try:
            while True:
                try:
                    schedule.run_pending()
                    
                    # Log active jobs periodically 
                    if len(self.active_jobs) > 0:
                        active_job_names = list(self.active_jobs.keys())
                        self.logger.debug(f"Active threaded jobs: {active_job_names}")
                    
                    # Heartbeat logging every 5 minutes
                    heartbeat_counter += 1
                    if heartbeat_counter >= 5:
                        self.logger.info("Scheduler heartbeat: System running normally")
                        # Log next scheduled runs
                        for job in schedule.get_jobs():
                            job_name = getattr(job.job_func, '__name__', 'unknown_job')
                            self.logger.info(f"Next {job_name} run: {job.next_run}")
                        heartbeat_counter = 0
                    
                except Exception as e:
                    self.logger.error(f"Scheduler loop error: {e}", exc_info=True)
                    # Continue running despite individual loop errors
                
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("Shutting down automated trader...")
            self.shutdown()
        except Exception as e:
            self.logger.error(f"Fatal main loop error: {e}")
            self.shutdown()
            raise

    def shutdown(self):
        """Gracefully shutdown the trader and thread pool"""
        self.logger.info("Shutting down thread pool...")
        
        # Wait for running jobs to complete (with timeout)
        if self.active_jobs:
            self.logger.info(f"Waiting for {len(self.active_jobs)} jobs to complete...")
            for job_name, future in self.active_jobs.items():
                try:
                    future.result(timeout=30)  # 30 second timeout per job
                    self.logger.info(f"Job {job_name} completed during shutdown")
                except Exception as e:
                    self.logger.warning(f"Job {job_name} failed during shutdown: {e}")
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        self.logger.info("Thread pool shutdown complete")

def main():
    """Main entry point"""
    config = TradingConfig()
    trader = AutomatedTrader(config)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "run-once":
            # Run daily cycle once for testing
            trader.run_daily_cycle()
        elif sys.argv[1] == "run-once-research":
            # Run research cycle once for testing
            trader.run_opening_cycle()
        else:
            print("Usage: python automated_trader.py [run-once|run-once-research]")
    else:
        # Start automated schedule
        trader.start_automated_trading()

if __name__ == "__main__":
    main()
