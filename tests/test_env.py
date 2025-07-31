#!/usr/bin/env python3
"""
Test script to verify environment setup
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def test_environment():
    """Test if all required environment variables are set"""
    required_vars = [
        'OPENAI_API_KEY',
        'ALPACA_API_KEY', 
        'ALPACA_SECRET_KEY',
        'EMAIL_FROM',
        'EMAIL_TO'
    ]
    
    print("🧪 Testing Environment Setup...")
    print("=" * 50)
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: Missing")
        else:
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {var}: {masked_value}")
    
    print("=" * 50)
    
    if missing_vars:
        print(f"❌ Missing required variables: {', '.join(missing_vars)}")
        print("\n📝 Please edit your .env file and add these variables.")
        print("📖 See .env.example for the format.")
        return False
    else:
        print("✅ All environment variables configured!")
        return True

def test_imports():
    """Test if all required libraries are installed"""
    print("\n🔧 Testing Library Imports...")
    print("=" * 50)
    
    libraries = [
        ('yfinance', 'yfinance'),
        ('openai', 'openai'),
        ('alpaca_trade_api', 'alpaca_trade_api'),
        ('pydantic', 'pydantic'),
        ('pandas', 'pandas')
    ]
    
    success = True
    for lib_name, import_name in libraries:
        try:
            __import__(import_name if import_name != lib_name else lib_name)
            print(f"✅ {lib_name}: Imported successfully")
        except ImportError as e:
            print(f"❌ {lib_name}: Import failed - {e}")
            success = False
    
    print("=" * 50)
    return success

def test_market_data():
    """Test yfinance market data"""
    print("\n📊 Testing Market Data Access...")
    print("=" * 50)
    
    try:
        import yfinance as yf
        
        # Test getting data for a simple ticker
        ticker = yf.Ticker("AAPL")
        data = ticker.history(period="1d")
        
        if not data.empty:
            price = data['Close'].iloc[-1]
            print(f"✅ Market data working - AAPL: ${price:.2f}")
            return True
        else:
            print("❌ Market data returned empty")
            return False
            
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Automated Trading Bot - Environment Test")
    print("=" * 50)
    
    env_ok = test_environment()
    imports_ok = test_imports()
    data_ok = test_market_data()
    
    print("\n" + "=" * 50)
    if env_ok and imports_ok and data_ok:
        print("🎉 ALL TESTS PASSED! Ready to deploy!")
        print("\n📋 Next steps:")
        print("1. ✅ Environment setup complete")
        print("2. 🚀 Deploy to Railway or test locally")
        print("3. 📧 Check email for daily reports")
    else:
        print("❌ Some tests failed. Please fix issues before deploying.")
        
        if not env_ok:
            print("🔧 Fix: Edit .env file with your API keys")
        if not imports_ok:
            print("🔧 Fix: Run 'pip3 install -r requirements.txt'")
        if not data_ok:
            print("🔧 Fix: Check internet connection")

if __name__ == "__main__":
    main()
