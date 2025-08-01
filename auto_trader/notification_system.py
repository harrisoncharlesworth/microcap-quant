"""
Notification System for automated trading alerts
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from .config import TradingConfig
from .ai_decision_engine import TradingDecision

class NotificationSystem:
    def __init__(self, config: TradingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def _send_email(self, subject: str, body: str):
        """Send email notification if configured"""
        if not self.config.email_alerts or not self.config.email_to:
            return
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.email_from or self.config.smtp_username
            msg['To'] = self.config.email_to
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            if self.config.smtp_username and self.config.smtp_password:
                server.login(self.config.smtp_username, self.config.smtp_password)
            
            text = msg.as_string()
            server.sendmail(msg['From'], msg['To'], text)
            server.quit()
            
            self.logger.info(f"Email sent successfully: {subject}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
    
    def send_daily_report(self, decisions: List[TradingDecision], performance: Dict):
        """Send daily trading report"""
        actionable_decisions = [d for d in decisions if d.action in ["BUY", "SELL"]]
        
        subject = f"Daily Trading Report - {len(actionable_decisions)} Actions"
        
        body_lines = [
            f"Daily Trading Report",
            f"==================",
            f"Actionable Decisions: {len(actionable_decisions)}",
            f"Total Decisions: {len(decisions)}",
            ""
        ]
        
        if actionable_decisions:
            body_lines.append("Trading Actions:")
            for decision in actionable_decisions:
                body_lines.append(f"  {decision.action} {decision.ticker} - Confidence: {decision.confidence:.1%}")
                body_lines.append(f"    Reason: {decision.reasoning}")
                body_lines.append("")
        
        if performance:
            body_lines.extend([
                "Performance:",
                f"  Total Return: {performance.get('total_return', 0):.2%}",
                f"  Total Equity: ${performance.get('total_equity', 0):.2f}",
                ""
            ])
        
        body = "\n".join(body_lines)
        
        self.logger.info(f"Daily Report: {len(actionable_decisions)} actionable decisions made")
        self._send_email(subject, body)
    
    def send_custom_report(self, title: str, decisions: List[TradingDecision], performance: Dict):
        """Send custom report"""
        self.logger.info(f"{title}: {len(decisions)} decisions made")
        if performance:
            self.logger.info(f"Performance: {performance.get('total_return', 0):.2%} total return")
    
    def send_error_alert(self, error_message: str):
        """Send error alert"""
        subject = "Trading System Error Alert"
        body = f"Error in automated trading system:\n\n{error_message}"
        
        self.logger.error(f"Trading Error: {error_message}")
        self._send_email(subject, body)
    
    def send_startup_notification(self):
        """Send startup notification"""
        subject = "Trading System Started"
        body = "Automated trading system has started successfully and is now monitoring the markets."
        
        self.logger.info("Automated trading system started successfully")
        self._send_email(subject, body)
    
    def send_test_email(self):
        """Send test email to verify configuration"""
        import datetime
        
        subject = "Trading System Email Test"
        body = f"""This is a test email from your automated trading system.
        
Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Configuration: {self.config.smtp_server}:{self.config.smtp_port}
From: {self.config.email_from}
To: {self.config.email_to}

If you receive this email, your notification system is working correctly!"""
        
        self.logger.info("Sending test email...")
        self._send_email(subject, body)
