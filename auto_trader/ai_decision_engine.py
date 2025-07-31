"""
AI Decision Engine - Automates ChatGPT trading decisions
"""
import openai
import anthropic
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from config import TradingConfig

@dataclass
class TradingDecision:
    action: str  # "BUY", "SELL", "HOLD"
    ticker: str
    confidence: float  # 0-1
    reasoning: str
    position_size: Optional[float] = None  # For BUY orders
    target_price: Optional[float] = None

class AIDecisionEngine:
    def __init__(self, config: TradingConfig):
        self.config = config
        self.openai_client = openai.OpenAI(api_key=config.openai_api_key)
        self.anthropic_client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self.logger = logging.getLogger(__name__)
        
    def make_daily_decisions(self, portfolio_data: Dict, market_data: Dict) -> List[TradingDecision]:
        """Make daily trading decisions based on portfolio and market data"""
        prompt = self._build_daily_prompt(portfolio_data, market_data)
        
        try:
            response = self._call_ai_model(prompt, self.config.primary_model)
            decisions = self._parse_decisions(response)
            self.logger.info(f"AI made {len(decisions)} trading decisions")
            return decisions
        except Exception as e:
            self.logger.error(f"Primary model failed: {e}")
            # Fallback to backup model
            try:
                response = self._call_ai_model(prompt, self.config.backup_model)
                decisions = self._parse_decisions(response)
                self.logger.warning(f"Used backup model, made {len(decisions)} decisions")
                return decisions
            except Exception as e2:
                self.logger.error(f"Both models failed: {e2}")
                return []
    
    def make_weekly_research(self, portfolio_data: Dict) -> List[TradingDecision]:
        """Make weekly deep research decisions"""
        prompt = self._build_research_prompt(portfolio_data)
        
        try:
            response = self._call_ai_model(prompt, self.config.primary_model, max_tokens=2000)
            decisions = self._parse_decisions(response)
            self.logger.info(f"Weekly research generated {len(decisions)} decisions")
            return decisions
        except Exception as e:
            self.logger.error(f"Weekly research failed: {e}")
            return []
    
    def _build_daily_prompt(self, portfolio_data: Dict, market_data: Dict) -> str:
        """Build the daily trading prompt"""
        portfolio_summary = self._format_portfolio(portfolio_data)
        market_summary = self._format_market_data(market_data)
        
        prompt = f"""You are a professional portfolio strategist managing a micro-cap stock portfolio.

CURRENT PORTFOLIO:
{portfolio_summary}

TODAY'S MARKET DATA:
{market_summary}

RULES:
- Only trade micro-cap stocks (market cap under $300M)
- Maximum 15% position size per stock
- Strict 15% stop-loss rules apply
- Focus on generating alpha vs Russell 2000

TASK: Analyze the current data and decide on ANY actions needed today. For each decision, provide:
1. ACTION: BUY/SELL/HOLD
2. TICKER: Stock symbol
3. CONFIDENCE: 0.0-1.0
4. REASONING: Brief explanation
5. POSITION_SIZE: For buys only (% of portfolio)

Respond in JSON format:
{{
  "decisions": [
    {{
      "action": "BUY",
      "ticker": "EXAMPLE",
      "confidence": 0.8,
      "reasoning": "Strong momentum and volume spike",
      "position_size": 0.10
    }}
  ]
}}"""
        return prompt
    
    def _build_research_prompt(self, portfolio_data: Dict) -> str:
        """Build the weekly research prompt"""
        portfolio_summary = self._format_portfolio(portfolio_data)
        
        prompt = f"""You are a professional portfolio analyst conducting weekly deep research.

CURRENT PORTFOLIO:
{portfolio_summary}

Use deep research capabilities to:
1. Evaluate current holdings for continued strength
2. Identify new micro-cap opportunities (market cap under $300M)
3. Consider macro trends affecting small caps
4. Analyze relative performance vs benchmarks

Make strategic decisions for the week ahead. You have complete control to buy, sell, or hold.

Respond in JSON format with your decisions and provide a thesis summary:
{{
  "decisions": [
    {{
      "action": "BUY",
      "ticker": "EXAMPLE", 
      "confidence": 0.85,
      "reasoning": "Deep research shows strong fundamentals",
      "position_size": 0.12
    }}
  ],
  "thesis_summary": "Brief summary of your investment thesis for next week"
}}"""
        return prompt
    
    def _call_ai_model(self, prompt: str, model: str, max_tokens: int = 1000) -> str:
        """Call the specified AI model"""
        if model.startswith("gpt"):
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        
        elif model.startswith("claude"):
            response = self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        else:
            raise ValueError(f"Unknown model: {model}")
    
    def _parse_decisions(self, response: str) -> List[TradingDecision]:
        """Parse AI response into trading decisions"""
        try:
            data = json.loads(response)
            decisions = []
            
            for decision_data in data.get("decisions", []):
                decision = TradingDecision(
                    action=decision_data.get("action", "HOLD").upper(),
                    ticker=decision_data.get("ticker", "").upper(),
                    confidence=float(decision_data.get("confidence", 0.5)),
                    reasoning=decision_data.get("reasoning", ""),
                    position_size=decision_data.get("position_size"),
                    target_price=decision_data.get("target_price")
                )
                
                # Validate decision
                if decision.action in ["BUY", "SELL", "HOLD"] and decision.ticker:
                    decisions.append(decision)
                    
            return decisions
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse AI response: {e}")
            return []
    
    def _format_portfolio(self, portfolio_data: Dict) -> str:
        """Format portfolio data for prompt"""
        lines = []
        for position in portfolio_data.get("positions", []):
            lines.append(f"- {position['ticker']}: {position['shares']} shares @ ${position['buy_price']:.2f}")
        
        lines.append(f"Cash: ${portfolio_data.get('cash', 0):.2f}")
        lines.append(f"Total Equity: ${portfolio_data.get('total_equity', 0):.2f}")
        
        return "\n".join(lines)
    
    def _format_market_data(self, market_data: Dict) -> str:
        """Format market data for prompt"""
        lines = []
        for ticker, data in market_data.items():
            price = data.get("price", 0)
            change = data.get("percent_change", 0)
            volume = data.get("volume", 0)
            lines.append(f"- {ticker}: ${price:.2f} ({change:+.2f}%) Vol: {volume:,.0f}")
        
        return "\n".join(lines)
