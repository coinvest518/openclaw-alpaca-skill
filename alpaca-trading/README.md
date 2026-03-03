# Alpaca Trading OpenClaw Skill

Drop this folder into `~/.openclaw/skills/alpaca-trading` or keep it
in your workspace under `skills/` for per-agent loading.

Install
```bash
pip install -r /path/to/alpaca-trading/requirements.txt
cp /path/to/alpaca-trading/.env.example /path/to/alpaca-trading/.env
# edit .env with your Alpaca keys
```

Quick examples
```bash
python agent.py "account"
python agent.py "positions"
python agent.py "quote AAPL"
python agent.py "analyse AAPL"
python agent.py "buy 3 AAPL"
```

Notes
- Paper trading is enabled by default. Live trades require `ALPACA_PAPER=false`
  in `.env` and the word `confirm` in your command (safety guard).
