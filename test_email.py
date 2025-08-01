#!/usr/bin/env python3
"""
Test script to verify email notifications are working
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auto_trader.config import TradingConfig
from auto_trader.notification_system import NotificationSystem

def test_email():
    """Test email notification functionality"""
    print("Testing email notification system...")
    
    # Load configuration
    config = TradingConfig()
    
    # Check if email is configured
    if not config.email_to:
        print("❌ EMAIL_TO not configured in .env file")
        return False
    
    if not config.smtp_password:
        print("❌ EMAIL_PASSWORD not configured in .env file")
        return False
    
    print(f"📧 Email configured:")
    print(f"   From: {config.email_from}")
    print(f"   To: {config.email_to}")
    print(f"   SMTP: {config.smtp_server}:{config.smtp_port}")
    print()
    
    # Initialize notification system
    notifications = NotificationSystem(config)
    
    # Send test email
    print("📤 Sending test email...")
    notifications.send_test_email()
    print("✅ Test email sent! Check your inbox.")
    
    return True

if __name__ == "__main__":
    success = test_email()
    if success:
        print("\n🎉 Email test completed successfully!")
    else:
        print("\n❌ Email test failed - check configuration")
        sys.exit(1)
