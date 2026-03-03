[![GitHub Stars](https://img.shields.io/github/stars/coinvest518/openclaw-alpaca-skill?style=social)](https://github.com/coinvest518/openclaw-alpaca-skill/stargazers)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#)

# Alpaca Trading OpenClaw Skill

Lightweight Alpaca trading and technical analysis for OpenClaw agents. Paper trading by default.

Quick links
- OpenClaw: https://github.com/openclaw
- Alpaca Markets: https://alpaca.markets
- Python: https://python.org/

## 📋 Full checklist (before installing the skill)
1. Python 3.10+ installed (install from python.org)
2. Alpaca account created at https://alpaca.markets (free paper trading available)
3. Alpaca API keys generated from dashboard (Keys & Secrets section)
4. OpenClaw installed (if using global skills directory)
5. Decided on paper vs. live trading mode

## Installing the skill
1. Copy `alpaca-trading/` folder to your OpenClaw skills directory (example: `~/.openclaw/skills/`).
2. Install Python dependencies: `pip install -r alpaca-trading/requirements.txt`
3. Create `.env` from the included `.env.example` and paste your Alpaca API key and secret.
4. Restart OpenClaw gateway: `openclaw gateway restart`
5. Verify: `openclaw skills list | grep alpaca` (should appear)

## 🔐 How the trading safety works
WITHOUT live mode confirmation (safe):
- Default is paper trading → all orders execute in simulated environment ✅
- Your real money is never at risk ✅

WITH live mode (requires explicit opt-in):
- Set `ALPACA_PAPER=false` in `.env` file
- Use `confirm` keyword in commands to execute real trades
- Orders execute against your real brokerage account ⚠️

## Folder structure (final)
```
~/.openclaw/skills/
└── alpaca-trading/
    ├── SKILL.md         ← OpenClaw metadata (loads skill automatically)
    ├── README.md        ← this document
    ├── agent.py         ← CLI agent with natural-language router
    ├── alpaca_client.py ← REST API wrapper
    ├── indicators.py    ← technical analysis (pandas-based)
    ├── requirements.txt ← Python dependencies
    └── .env.example     ← template for API keys
```

## Capabilities
- Query account info and buying power
- List open positions and portfolio
- Submit market orders (paper by default)
- Fetch real-time quotes (latest bar data)
- Technical analysis: EMA, RSI, ATR, MACD, Bollinger Bands, VWAP
- Historical bar data retrieval

## Restrictions (safety defaults)
- Live trading DISABLED by default
- Limit orders NOT implemented (market orders only)
- Stop-loss and bracket orders NOT implemented
- No automated position management

## Usage

When a user asks about trading or analysis:

1. Run the agent:
```bash
cd ~/.openclaw/skills/alpaca-trading && python agent.py "<user request>"
```
2. Parse the JSON response and present results clearly.
3. If executing trades, confirm paper vs. live mode.

## Examples
- "Show my account" → fetch account info and buying power
- "What positions do I have?" → list current positions
- "Quote AAPL" → get latest price and bar data
- "Analyze TSLA" → run technical indicators on recent bars
- "Buy 5 AAPL" → submit market order (paper mode)

## Security & disclaimers
- ⚠️ This skill can execute REAL trades when `ALPACA_PAPER=false`
- Never store live API keys in public repositories
- Use environment variables or secret vault for production
- This is provided as-is; trading carries financial risk
- Not financial advice

## Files added by this package
- `alpaca-trading/.env.example` — shows `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` placeholders
- `alpaca-trading/SKILL.md` — metadata for OpenClaw skill discovery
- `alpaca-trading/agent.py` — minimal CLI agent with command router
- `alpaca-trading/alpaca_client.py` — REST client for Alpaca API
- `alpaca-trading/indicators.py` — pandas-based technical analysis functions
- `alpaca-trading/requirements.txt` — Python dependencies (alpaca-py, pandas, requests)

