"""
Notification System for automated trading alerts
"""
import logging
from typing import Dict, List
from config import TradingConfig
from .ai_decision_engine import TradingDecision

class NotificationSystem:
    def __init__(self, config: TradingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def send_daily_report(self, decisions: List[TradingDecision], performance: Dict):
        """Send daily trading report"""
        self.logger.info(f"Daily Report: {len(decisions)} decisions made")
        if performance:
            self.logger.info(f"Performance: {performance.get('total_return', 0):.2%} total return")
    
    def send_custom_report(self, title: str, decisions: List[TradingDecision], performance: Dict):
        """Send custom report"""
        self.logger.info(f"{title}: {len(decisions)} decisions made")
        if performance:
            self.logger.info(f"Performance: {performance.get('total_return', 0):.2%} total return")
    
    def send_error_alert(self, error_message: str):
        """Send error alert"""
        self.logger.error(f"Trading Error: {error_message}")
    
    def send_startup_notification(self):
        """Send startup notification"""
        self.logger.info("Automated trading system started successfully")
