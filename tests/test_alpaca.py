#!/usr/bin/env python3
"""
Test Alpaca API connection and paper trading
"""

import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

# Load environment variables
load_dotenv()

def test_alpaca_connection():
    """Test Alpaca API connection and account info"""
    print("🧪 Testing Alpaca Paper Trading Connection...")
    print("=" * 50)
    
    # Get credentials
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    paper_trading = os.getenv("PAPER_TRADING", "true").lower() == "true"
    
    if not api_key or not secret_key:
        print("❌ Missing Alpaca API keys")
        return False
    
    try:
        # Initialize API
        base_url = 'https://paper-api.alpaca.markets' if paper_trading else 'https://api.alpaca.markets'
        api = tradeapi.REST(api_key, secret_key, base_url=base_url, api_version='v2')
        
        print(f"✅ Connected to: {'Paper Trading' if paper_trading else 'Live Trading'}")
        
        # Get account info
        account = api.get_account()
        print(f"✅ Account Status: {account.status}")
        print(f"✅ Buying Power: ${float(account.buying_power):,.2f}")
        print(f"✅ Cash: ${float(account.cash):,.2f}")
        print(f"✅ Portfolio Value: ${float(account.portfolio_value):,.2f}")
        
        # Test getting positions
        positions = api.list_positions()
        print(f"✅ Current Positions: {len(positions)}")
        
        # Test a simple stock lookup
        try:
            asset = api.get_asset('AAPL')
            print(f"✅ Asset lookup working: AAPL is {asset.status}")
        except Exception as e:
            print(f"⚠️  Asset lookup issue: {e}")
        
        # Test a market order (small amount to test)
        print("\n🧪 Testing Paper Trade Execution...")
        try:
            # Submit a small test order
            test_order = api.submit_order(
                symbol='AAPL',
                qty=1,
                side='buy',
                type='market',
                time_in_force='day'
            )
            print(f"✅ Test order submitted: {test_order.id}")
            print(f"✅ Order status: {test_order.status}")
            
            # Cancel the order immediately
            api.cancel_order(test_order.id)
            print("✅ Test order cancelled successfully")
            
        except Exception as e:
            print(f"❌ Order execution failed: {e}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Alpaca connection fully working!")
        return True
        
    except Exception as e:
        print(f"❌ Alpaca connection failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Alpaca Paper Trading Test")
    print("=" * 50)
    
    success = test_alpaca_connection()
    
    if success:
        print("\n✅ Ready for automated trading!")
    else:
        print("\n❌ Fix Alpaca connection before deploying")
        print("\n🔧 Possible fixes:")
        print("- Verify your Alpaca API keys are correct")
        print("- Make sure you're using Paper Trading keys")
        print("- Check if your Alpaca account is approved")

if __name__ == "__main__":
    main()
