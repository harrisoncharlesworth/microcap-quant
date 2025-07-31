#!/usr/bin/env python3
"""
Test script for configuration only (no API calls)
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add auto_trader to path
sys.path.append('auto_trader')

from auto_trader.config import TradingConfig

def test_config():
    """Test the configuration setup"""
    print("Testing Configuration...")
    
    # Initialize config
    config = TradingConfig()
    
    print(f"✅ Primary Model: {config.primary_model}")
    print(f"✅ Deep Research Model: {config.deep_research_model}")
    print(f"✅ Market Open Time: {config.market_open_time}")
    print(f"✅ Trading Time: {config.trading_time}")
    print(f"✅ Data Directory: {config.data_dir}")
    
    # Check API key configuration
    if config.openai_api_key:
        print(f"✅ OpenAI API Key: {'*' * (len(config.openai_api_key) - 4)}{config.openai_api_key[-4:]}")
    else:
        print("⚠️  OpenAI API Key: Not configured")
    
    print("\n🎯 Configuration Summary:")
    print(f"   • 09:30 EST Deep Research: {config.deep_research_model}")
    print(f"   • 16:30 EST Daily Trading: {config.primary_model}")
    print(f"   • Backup Model: {config.backup_model}")
    
    print("\n✅ Configuration test completed successfully!")

if __name__ == "__main__":
    test_config()
