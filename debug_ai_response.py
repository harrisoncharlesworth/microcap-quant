#!/usr/bin/env python3
"""
Debug script to see the AI's trading reasoning
"""

import os
import json
import yfinance as yf
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_ai_reasoning():
    """Get the AI's current trading analysis and reasoning"""
    
    # Initialize OpenAI
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Get current market data for benchmarks
    tickers = ["^RUT", "IWO", "XBI"]
    market_data = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            
            if len(hist) >= 2:
                current_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[-2])
                volume = float(hist['Volume'].iloc[-1])
                pct_change = ((current_price - prev_price) / prev_price) * 100
                
                market_data[ticker] = {
                    'price': current_price,
                    'pct_change': pct_change,
                    'volume': volume
                }
        except:
            pass
    
    # Format market data for prompt
    market_lines = []
    for ticker, data in market_data.items():
        market_lines.append(f"- {ticker}: ${data['price']:.2f} ({data['pct_change']:+.2f}%) Vol: {data['volume']:,.0f}")
    
    # Build prompt (simplified version of the trading prompt)
    prompt = f"""You are managing a micro-cap stock portfolio. Analyze today's data and make trading decisions.

CURRENT PORTFOLIO ($1000 total equity):
- No positions
Cash: $1000.00

TODAY'S MARKET DATA:
{chr(10).join(market_lines)}

RULES:
- Only trade micro-cap stocks (market cap under $300M)
- Maximum 15% position size per stock
- 15% stop losses are automatically set
- Focus on generating alpha vs Russell 2000
- You MUST deploy capital - holding cash is failure

SUGGESTED MICRO-CAP RESEARCH AREAS:
- Small biotech/pharma companies with upcoming catalysts
- Technology companies with innovative products  
- Energy/mining companies with growth potential
- Small regional banks or specialty finance
- Consumer companies with niche products

EXAMPLE VALID MICRO-CAP TICKERS (verify current status):
ABEO, IINN, ACTU, BBAI, CDZI, FREQ, MVIS, RGTI, SNDX, VERB

Respond with trading decisions in JSON format:
{{
  "orders": [
    {{
      "action": "BUY",
      "ticker": "EXAMPLE",
      "qty": 10,
      "reasoning": "Strong momentum and volume",
      "confidence": 0.8
    }}
  ],
  "market_analysis": "Brief analysis of market conditions",
  "risk_assessment": "Current risk level assessment"
}}

IMPORTANT: You must deploy capital and make trades. Holding cash is not allowed.
Your goal is to find the best micro-cap opportunities and invest the portfolio.
You should typically make 2-4 BUY orders to diversify unless market conditions are extremely poor."""

    # Get AI response
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.3
        )
        
        content = response.choices[0].message.content or ""
        return content
        
    except Exception as e:
        return f"Error getting AI response: {e}"

def main():
    """Display the AI's reasoning"""
    print("🤖 AI Trading Analysis & Reasoning")
    print("=" * 60)
    
    reasoning = get_ai_reasoning()
    
    # Try to parse JSON to show structured output
    try:
        # Find JSON in response
        start_idx = reasoning.find('{')
        end_idx = reasoning.rfind('}') + 1
        
        if start_idx != -1 and end_idx != 0:
            json_str = reasoning[start_idx:end_idx]
            data = json.loads(json_str)
            
            print("📊 MARKET ANALYSIS:")
            print(data.get('market_analysis', 'Not provided'))
            print()
            
            print("⚠️  RISK ASSESSMENT:")
            print(data.get('risk_assessment', 'Not provided'))
            print()
            
            print("💰 TRADING DECISIONS:")
            orders = data.get('orders', [])
            for i, order in enumerate(orders, 1):
                print(f"{i}. {order['action']} {order['ticker']} - {order['qty']} shares")
                print(f"   Reasoning: {order['reasoning']}")
                print(f"   Confidence: {order.get('confidence', 'N/A')}")
                print()
            
        else:
            print("Raw AI Response:")
            print(reasoning)
            
    except Exception as e:
        print("Raw AI Response (couldn't parse JSON):")
        print(reasoning)
        print(f"\nParsing error: {e}")

if __name__ == "__main__":
    main()
