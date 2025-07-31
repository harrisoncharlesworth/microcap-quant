# Environment Variables Configuration

This document lists all environment variables used by the micro-cap trading system.

## AI Model Configuration

### Required API Keys
- `OPENAI_API_KEY` - OpenAI API key for GPT models
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude models (optional)
- `GROQ_API_KEY` - Groq API key for Groq models (optional)

### Model Selection
- `AI_PRIMARY_MODEL` - Model for daily 16:30 cycle (default: `gpt-4o`)
- `AI_BACKUP_MODEL` - Fallback model if primary fails (default: `gpt-4`)
- `AI_RESEARCH_MODEL` - Model for deep research at 09:30 (default: `o3-deep-research-2025-06-26`)

### Supported Models
- **OpenAI**: `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`
- **OpenAI Deep Research**: `o3-deep-research-2025-06-26`, `o4-mini-deep-research-2025-06-26`
- **Anthropic**: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`
- **Groq**: `groq/llama3-70b-8192`, `groq/mixtral-8x7b-32768`

## Trading Configuration

- `ALPACA_API_KEY` - Alpaca trading API key
- `ALPACA_SECRET_KEY` - Alpaca trading secret key
- `PAPER_TRADING` - Set to `true` for paper trading, `false` for live (default: `true`)

## Email Notifications

- `EMAIL_FROM` - Sender email address
- `EMAIL_TO` - Recipient email address
- `EMAIL_PASSWORD` - Email account app password
- `SMTP_SERVER` - SMTP server (default: `smtp.gmail.com`)
- `SMTP_PORT` - SMTP port (default: `587`)

## Trading Parameters

- `STARTING_CASH` - Initial portfolio cash amount (default: `100`)
- `MAX_POSITION_PCT` - Maximum position size as % of portfolio (default: `0.15`)
- `STOP_LOSS_PCT` - Stop loss percentage (default: `0.15`)

## Example .env File

```env
# AI Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
AI_PRIMARY_MODEL=gpt-4o
AI_RESEARCH_MODEL=o3-deep-research-2025-06-26

# Trading
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
PAPER_TRADING=true

# Email
EMAIL_FROM=bot@yourdomain.com
EMAIL_TO=you@yourdomain.com
EMAIL_PASSWORD=your_app_password
```

## Scheduling

The system runs two cycles:
- **09:30 EST**: Deep research using `AI_RESEARCH_MODEL` (default: o3-deep-research-2025-06-26)
- **16:30 EST**: Daily analysis using `AI_PRIMARY_MODEL` (default: gpt-4o)
