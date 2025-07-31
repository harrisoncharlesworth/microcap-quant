#!/usr/bin/env python3
"""
Test script for deep research functionality
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add auto_trader to path
sys.path.append('auto_trader')

from auto_trader.config import TradingConfig
from auto_trader.ai_decision_engine import AIDecisionEngine

def test_deep_research():
    """Test the deep research functionality"""
    print("Testing Deep Research Model Configuration...")
    
    # Initialize config
    config = TradingConfig()
    
    print(f"Primary Model: {config.primary_model}")
    print(f"Deep Research Model: {config.deep_research_model}")
    print(f"Market Open Time: {config.market_open_time}")
    
    # Initialize AI engine
    try:
        ai_engine = AIDecisionEngine(config)
        print("✅ AI Decision Engine initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AI engine: {e}")
        return
    
    # Test portfolio data
    test_portfolio = {
        'cash': 500.0,
        'total_equity': 1000.0,
        'positions': {
            'ABEO': {
                'shares': 100,
                'buy_price': 2.50,
                'stop_loss': 2.12
            }
        }
    }
    
    print("\nTesting Deep Research with sample portfolio...")
    try:
        decisions = ai_engine.make_deep_research(test_portfolio)
        print(f"✅ Deep research completed, generated {len(decisions)} decisions")
        
        for decision in decisions:
            print(f"  - {decision.action} {decision.ticker}: {decision.reasoning}")
            
        # Also test regular daily decisions as backup
        print("\nTesting fallback to daily decisions...")
        daily_decisions = ai_engine.make_daily_decisions(test_portfolio, {})
        print(f"✅ Daily decisions completed, generated {len(daily_decisions)} decisions")
        
        for decision in daily_decisions:
            print(f"  - {decision.action} {decision.ticker}: {decision.reasoning}")
            
    except Exception as e:
        print(f"❌ Deep research failed: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_deep_research()
