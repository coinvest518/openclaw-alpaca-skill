# Alpaca Trading OpenClaw Skill

Drop this folder into `~/.openclaw/skills/alpaca-trading` or keep it
in your workspace under `skills/` for per-agent loading.

Install
```bash
pip install -r /path/to/alpaca-trading/requirements.txt
cp /path/to/alpaca-trading/.env.example /path/to/alpaca-trading/.env
# edit .env with your Alpaca keys
# Alpaca Trading Skill

[![GitHub Stars](https://img.shields.io/github/stars/coinvest518/openclaw-alpaca-trading-skill?style=social)](https://github.com/coinvest518/openclaw-alpaca-trading-skill/stargazers)  
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#)

This OpenClaw skill provides a lightweight Alpaca trading integration and
technical analysis utilities. It supports common account queries, market and
limit orders (paper by default), simple market data fetching, and indicator
analysis (EMA, RSI, ATR, MACD, Bollinger Bands, VWAP).

Important safety notes

- Paper trading is the default. Live trading requires `ALPACA_PAPER=false`
  in your `.env` and explicit `confirm` in the same command to execute live
  orders. Review all orders before confirming — this skill may execute real
  trades when live mode is enabled.

## 📋 Checklist (before installing)
1. Python 3.10+ installed
2. Create an Alpaca account (https://alpaca.markets) and generate API keys
3. Copy `.env.example` → `.env` and populate `ALPACA_API_KEY` and
   `ALPACA_SECRET_KEY`
4. (Optional) Install into OpenClaw skills directory for global usage

## Installation

Copy the skill folder into your OpenClaw skills path (or keep it in your
workspace for per-agent loading) and install Python dependencies:

```bash
# copy into OpenClaw skills (optional)
cp -r ./alpaca-trading ~/.openclaw/skills/alpaca-trading

# install dependencies
pip install -r ./alpaca-trading/requirements.txt

# create .env and edit with your Alpaca keys
cp ./alpaca-trading/.env.example ./alpaca-trading/.env
```

To refresh skills in a running gateway:

```bash
openclaw gateway restart
# or
openclaw agent --message "refresh skills"
```

## 🔧 What this skill can do

- Query account info and buying power
- List open positions
- Submit simple market orders (paper by default)
- Fetch quick quotes (via latest bar)
- Run technical analysis on OHLCV bars: EMA, RSI, ATR, MACD, Bollinger Bands, VWAP

## Usage examples (CLI)

```bash
cd ./alpaca-trading
python agent.py "account"
python agent.py "positions"
python agent.py "quote AAPL"
python agent.py "analyse AAPL"
python agent.py "buy 5 AAPL"
```

## Files included

```
alpaca-trading/
├── SKILL.md        ← OpenClaw metadata + instructions
├── README.md       ← this document
├── agent.py        ← example CLI agent and natural-language router
├── alpaca_client.py← small Alpaca REST wrapper (requests)
├── indicators.py   ← pandas-based technical indicators
├── requirements.txt← Python dependencies
└── .env.example    ← template for your keys
```

## Development notes

- The `agent.py` is intentionally minimal — extend its parsing for more
  natural language phrases (dollar-based buys, limit/stop orders, bracket
  orders). Indicator logic lives in `indicators.py` and returns a compact
  dictionary suitable for Markdown output.

## Security & disclaimers

- This skill can execute trades when `ALPACA_PAPER=false`. Never store live
  keys in public repositories. Use environment variables or a secret vault.
- This is provided as-is; trading carries financial risk and this is not
  financial advice.

---

If you want, I can:
- expand the CLI to parse natural-language order phrases,
- add unit tests for `indicators.py`, or
- prepare a ClawHub package manifest for publishing.
