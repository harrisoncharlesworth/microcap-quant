# 🚂 Railway Deployment Guide

## 🚀 One-Click Deploy Your AI Trading Bot

### Step 1: Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

**OR manually:**

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select: `harrisoncharlesworth/microcap-quant`

### Step 2: Configure Environment Variables

In Railway dashboard → **Variables** tab, add these:

```bash
# AI Configuration
OPENAI_API_KEY=sk-proj-your-openai-key-here
AI_MODEL=gpt-4o-mini

# Trading Configuration  
ALPACA_API_KEY=your-alpaca-paper-key
ALPACA_SECRET_KEY=your-alpaca-paper-secret
PAPER_TRADING=true
STARTING_CASH=1000

# Email Notifications
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Risk Management (Optional - uses defaults if not set)
MAX_POSITION_PCT=0.15
SECTOR_MAX_PCT=0.40
MIN_DOLLAR_VOLUME=300000
BEAR_MAX_POSITION_PCT=0.07
```

### Step 3: Add Storage Volume

1. Railway dashboard → **Settings** tab
2. Click **"Add Volume"**
3. **Size**: 1GB (free tier)
4. **Mount Path**: `/app/data`

### Step 4: Set Timezone

1. In Railway dashboard → **Variables** tab
2. Add: `TZ=America/New_York`
3. *(Bot runs continuously with internal scheduling)*

### Step 5: Deploy & Monitor

1. Click **"Deploy"**
2. Watch build logs: Railway → **Deployments** tab
3. Monitor runtime: Railway → **Logs** tab
4. Check email for first trading report

## 📊 What Your Bot Does

### Daily Schedule (Monday-Friday):
1. **07:45 AM EST**: Pre-market deep research (o3-deep-research model)
2. **11:00 AM EST**: Intraday news refresh
3. **04:30 PM EST**: Daily trading decisions & execution
4. **Email Reports**: Performance summaries sent throughout day

### Safety Features Active:
- ✅ **Position Limits**: Max 15% per stock (reduced in bear markets)
- ✅ **Sector Limits**: Max 40% per sector
- ✅ **Liquidity Filters**: Min $300k daily volume
- ✅ **Market Regime Detection**: Adapts to bull/bear/sideways
- ✅ **Duplicate Prevention**: Won't double-buy existing positions

## 🛠️ Management

### View Performance:
- **Email Reports**: Daily summaries in your inbox
- **Railway Logs**: Real-time bot activity
- **Alpaca Dashboard**: Live portfolio at app.alpaca.markets

### Emergency Controls:
- **Pause Bot**: Railway dashboard → Service → Pause
- **Restart Bot**: Railway dashboard → Service → Restart
- **Update Config**: Railway dashboard → Variables → Edit

### Troubleshooting:
- **No Emails**: Check EMAIL_PASSWORD (Gmail app password)
- **No Trades**: Check Alpaca API keys are for paper trading
- **Build Fails**: Check Railway logs → Deployments tab

## 💰 Costs

- **Railway**: Free tier (limited hours) or $5/month Hobby plan
- **APIs**: 
  - OpenAI: ~$1-5/month
  - Alpaca: Free for paper trading
  - Gmail: Free
- **Total**: ~$5-10/month for fully automated trading

## 🔒 Security

- ✅ **API Keys**: Encrypted by Railway, never in public repo
- ✅ **Paper Trading**: No real money at risk initially
- ✅ **Risk Management**: Multiple safety layers prevent bad trades
- ✅ **Email Alerts**: Immediate notification of all activity

## ⚡ Going Live

When ready for real money:
1. Set `PAPER_TRADING=false`
2. Get live Alpaca API keys (not paper keys)
3. Update `STARTING_CASH` to your real amount
4. Restart deployment
5. Monitor closely for first week

---

**Questions?** Check Railway logs first, then email with screenshots of any errors.
