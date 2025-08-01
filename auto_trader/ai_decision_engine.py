"""
AI Decision Engine - Automates AI trading decisions with multiple model support
"""
import openai
import anthropic
import groq
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .config import TradingConfig

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
        try:
            self.anthropic_client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        except:
            self.anthropic_client = None
        try:
            self.groq_client = groq.Groq(api_key=config.groq_api_key)
        except:
            self.groq_client = None
        self.logger = logging.getLogger(__name__)
        
    def make_daily_decisions(self, portfolio_data: Dict, market_data: Dict) -> List[TradingDecision]:
        """Make daily trading decisions based on portfolio and market data"""
        prompt = self._build_daily_prompt(portfolio_data, market_data)
        
        try:
            response = self._call_ai_model(prompt, self.config.primary_model, max_tokens=2000)
            decisions = self._parse_decisions(response)
            actionable_decisions = [d for d in decisions if d.action in ["BUY", "SELL"]]
            self.logger.info(f"AI made {len(actionable_decisions)} actionable trading decisions (total: {len(decisions)})")
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
    
    def make_deep_research(self, portfolio_data: Dict) -> List[TradingDecision]:
        """Make deep research decisions using the research model at market open"""
        prompt = self._build_research_prompt(portfolio_data)
        mdl = self.config.deep_research_model or self.config.primary_model
        
        try:
            response = self._call_ai_model(prompt, mdl, max_tokens=2000)
            decisions = self._parse_decisions(response)
            self.logger.info(f"Deep research ({mdl}) generated {len(decisions)} decisions")
            return decisions
        except Exception as e:
            self.logger.error(f"Deep research failed: {e}")
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
        """Build the deep research prompt optimized for o3-deep-research"""
        portfolio_summary = self._format_portfolio(portfolio_data)
        
        prompt = f"""I need comprehensive market research and investment analysis for my micro-cap portfolio.

CURRENT PORTFOLIO STATUS:
{portfolio_summary}

RESEARCH OBJECTIVES:
1. Conduct thorough analysis of current holdings using latest financial data, SEC filings, and earnings reports
2. Identify 3-5 new micro-cap investment opportunities (market cap under $300M) with strong fundamentals
3. Analyze macro trends affecting small-cap stocks and sector rotation patterns
4. Compare performance metrics against Russell 2000 and sector benchmarks
5. Assess risk factors including liquidity, volatility, and market sentiment

REQUIRED ANALYSIS:
- Financial metrics: P/E ratios, revenue growth, debt levels, cash flow
- Recent news, earnings, and analyst coverage
- Technical analysis: price trends, volume patterns, support/resistance levels
- Sector analysis and competitive positioning
- Management quality and insider trading activity

Please provide specific data including current prices, target prices, and risk assessments. Include charts and tables where relevant. 

DELIVERABLE FORMAT:
Provide trading recommendations in JSON format with detailed reasoning:
{{
  "decisions": [
    {{
      "action": "BUY/SELL/HOLD",
      "ticker": "TICKER",
      "confidence": 0.0-1.0,
      "reasoning": "Detailed analysis with specific data points",
      "position_size": 0.XX,
      "target_price": 0.XX,
      "stop_loss": 0.XX
    }}
  ],
  "market_analysis": "Comprehensive market overview with data",
  "risk_assessment": "Portfolio risk analysis with metrics",
  "thesis_summary": "Investment thesis for next trading period"
}}

Focus on actionable insights backed by quantitative data and reliable sources."""
        return prompt
    
    def _call_ai_model(self, prompt: str, model: str, max_tokens: int = 1000) -> str:
        """Route to correct provider based on model prefix"""
        if model.startswith("o3-deep-research"):
            # Use OpenAI Responses API for Deep Research
            try:
                response = self.openai_client.responses.create(
                    model=model,
                    input=[
                        {
                            "role": "developer",
                            "content": """You are a professional financial analyst and micro-cap stock researcher. 
                            
Your task is to provide data-rich insights with specific figures, trends, and statistics. 
Focus on measurable outcomes and quantitative analysis. Use reliable financial sources like SEC filings, 
earnings reports, and established financial databases. Include inline citations and prioritize 
data-backed arguments for investment decisions.

Summarize findings in a structured format that could inform trading decisions, including specific 
price targets, risk assessments, and timing considerations."""
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    reasoning={"summary": "auto"},
                    tools=[{"type": "web_search_preview"}]
                )
                
                # Debug: print response structure for debugging
                self.logger.info(f"Deep Research Response: {response}")
                
                # Extract content from OpenAI responses API
                content = ""
                try:
                    if hasattr(response, 'output') and response.output:
                        # response.output is a list of ResponseOutputItem
                        for item in response.output:
                            # Check if this is a text response
                            if hasattr(item, 'type') and getattr(item, 'type', None) == 'text':
                                if hasattr(item, 'text'):
                                    content += getattr(item, 'text', '')
                            # Try to get any text content safely
                            item_str = str(item)
                            if item_str and item_str != str(type(item)):
                                content += item_str + "\n"
                except Exception as parse_error:
                    self.logger.error(f"Error parsing response output: {parse_error}")
                    content = str(response)
                
                self.logger.info(f"Deep Research Extracted Content: {content[:500]}...")
                
                # The o3 deep research model returns research analysis, not trading decisions
                # We need to parse insights and create a structured JSON response
                if content and not content.strip().startswith('{'):
                    # Convert research analysis to trading decision format
                    fallback_response = {
                        "decisions": [],
                        "analysis": content
                    }
                    return json.dumps(fallback_response)
                
                return content if content else "{\"decisions\": []}"
                    
            except Exception as e:
                self.logger.error(f"Deep Research API call failed: {e}")
                # Fallback to regular GPT model
                return self._call_ai_model(prompt, "gpt-4o", max_tokens)
        
        elif model.startswith("gpt"):
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=min(max_tokens, 4000),  # Increase limit to avoid truncation
                temperature=0.7
            )
            content = response.choices[0].message.content or ""
            self.logger.info(f"GPT model raw response: {content[:500]}...")
            
            # If the response isn't JSON, wrap it as analysis
            if content and not content.strip().startswith('{'):
                fallback_response = {
                    "decisions": [],
                    "analysis": content
                }
                return json.dumps(fallback_response)
            
            return content
        
        elif model.startswith("claude"):
            if not self.anthropic_client:
                raise ValueError("Anthropic client not initialized - check ANTHROPIC_API_KEY")
            response = self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        elif model.startswith("groq/"):
            if not self.groq_client:
                raise ValueError("Groq client not initialized - check GROQ_API_KEY")
            groq_model = model.split("/", 1)[1]  # e.g. groq/llama3-70b-8192
            response = self.groq_client.chat.completions.create(
                model=groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content or ""
        
        else:
            raise ValueError(f"Unknown model family: {model}")
    
    def _parse_decisions(self, response: str) -> List[TradingDecision]:
        """Parse AI response into trading decisions"""
        try:
            # Try to extract JSON from response if it's embedded in text
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                
                # Fix common JSON issues
                json_str = json_str.replace('...', '')  # Remove truncation indicators
                
                # Try to find complete JSON objects
                brace_count = 0
                valid_end = start
                for i, char in enumerate(json_str):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            valid_end = i + 1
                            break
                
                if valid_end > start:
                    json_str = json_str[:valid_end]
            else:
                json_str = response
            
            data = json.loads(json_str)
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
            
            # Count only actionable decisions (BUY/SELL) for logging
            actionable_decisions = [d for d in decisions if d.action in ["BUY", "SELL"]]
            if len(decisions) != len(actionable_decisions):
                self.logger.info(f"Total decisions: {len(decisions)} (including {len(decisions) - len(actionable_decisions)} HOLD decisions)")
                    
            return decisions
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse AI response: {e}")
            return []
    
    def _format_portfolio(self, portfolio_data: Dict) -> str:
        """Format portfolio data for prompt"""
        lines = []
        positions = portfolio_data.get("positions", {})
        
        # Handle both dict and list formats
        if isinstance(positions, dict):
            for ticker, position in positions.items():
                shares = position.get('shares', 0)
                buy_price = position.get('buy_price', position.get('avg_entry_price', position.get('avg_price', 0)))
                lines.append(f"- {ticker}: {shares} shares @ ${buy_price:.2f}")
        elif isinstance(positions, list):
            for position in positions:
                ticker = position.get('ticker', 'UNKNOWN')
                shares = position.get('shares', 0)
                buy_price = position.get('buy_price', position.get('avg_entry_price', position.get('avg_price', 0)))
                lines.append(f"- {ticker}: {shares} shares @ ${buy_price:.2f}")
        
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
