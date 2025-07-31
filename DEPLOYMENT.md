# 🚀 Automated Trading Bot - Zero-Maintenance Deployment

Deploy your micro-cap trading bot in 10 minutes with **zero technical knowledge required**.

## ✅ What You'll Get

- **Fully automated trading** - Runs daily at 4:30 PM EST
- **AI-powered decisions** - ChatGPT analyzes markets and makes trades
- **Email reports** - Daily performance summaries sent to your inbox
- **Stop-loss protection** - Automatic 15% stop losses on all positions
- **Paper trading mode** - Test safely before going live
- **Zero maintenance** - Cloud-hosted, auto-restarts, bulletproof

## 🎯 One-Click Deployment on Railway

### Step 1: Get Your API Keys

Before deploying, collect these API keys:

**OpenAI API Key**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account → API Keys → Create new key
3. Copy the key (starts with `sk-`)

**Alpaca Trading API Keys**
1. Go to [alpaca.markets](https://alpaca.markets)
2. Create account → Paper Trading → API Keys
3. Copy both API Key and Secret Key

**Gmail App Password** (for email reports)
1. Gmail → Manage Google Account → Security → 2-Step Verification
2. App Passwords → Generate password for "Mail"
3. Copy the 16-character password

### Step 2: Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

1. **Click the Railway button above**
2. **Fill in your environment variables:**

```
OPENAI_API_KEY = sk-your-openai-key
ALPACA_API_KEY = your-alpaca-key  
ALPACA_SECRET_KEY = your-alpaca-secret
EMAIL_FROM = your-email@gmail.com
EMAIL_TO = your-email@gmail.com
EMAIL_PASSWORD = your-gmail-app-password
STARTING_CASH = 1000
```

3. **Click "Deploy"**
4. **Add Storage:** In Railway dashboard → Add Volume → 1GB
5. **Schedule:** Settings → Cron → `30 21 * * 1-5` (runs Mon-Fri 4:30PM EST)

### Step 3: Monitor & Control

**Check Status:**
- Railway dashboard shows if bot is running
- Check email for daily reports
- View logs in Railway console

**Emergency Stop:**
- Railway dashboard → Pause service
- Bot immediately stops trading

**Restart:**
- Railway dashboard → Restart service  
- Bot resumes with saved state

## 📊 Alternative: Render Deployment

If you prefer Render over Railway:

1. Fork this repository
2. Connect to [render.com](https://render.com)
3. Create Web Service → Connect repo
4. Add environment variables in Render dashboard
5. Deploy

## 🛡️ Safety Features

- **Paper Trading Default** - Always starts in simulation mode
- **Stop Losses** - Automatic 15% protection on all positions  
- **Position Limits** - Maximum 15% per stock
- **Circuit Breaker** - Stops trading if daily loss > 5%
- **Email Alerts** - Immediate notification of errors
- **State Persistence** - Never loses portfolio data

## 🔧 Configuration Options

Edit these in Railway/Render environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PAPER_TRADING` | `true` | Set to `false` for live trading |
| `STARTING_CASH` | `1000` | Initial capital |
| `MAX_POSITION_PCT` | `0.15` | Max 15% per stock |
| `STOP_LOSS_PCT` | `0.15` | 15% stop loss |
| `AI_MODEL` | `gpt-4` | AI model to use |

## 📈 Going Live

When ready for real money:

1. Set `PAPER_TRADING=false` in environment variables
2. Get live Alpaca API keys (not paper keys)
3. Restart the service
4. Monitor first few trades closely

## 🚨 Troubleshooting

**Bot not trading?**
- Check Railway logs for errors
- Verify all API keys are correct
- Ensure cron schedule is set

**No email reports?**
- Check Gmail app password is correct
- Verify EMAIL_FROM and EMAIL_TO are set
- Check spam folder

**Need help?**
- Check Railway console logs
- Email support with error messages
- All activity is logged for debugging

## 💰 Costs

- **Railway:** Free tier (limited hours) or $5/month
- **Render:** Free tier or $7/month  
- **APIs:** OpenAI ~$1-5/month, Alpaca free
- **Total:** ~$5-15/month for fully automated trading

## 🔒 Security

- All API keys encrypted by Railway/Render
- No trading data stored externally  
- Only you have access to your bot
- State file backed up automatically

---

**Questions?** Check the logs first, then email with screenshots of any errors.
