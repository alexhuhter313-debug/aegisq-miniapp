# AEGISQ Mini App

Telegram Mini App + Docker backend for your security tools.

## Quick Start

```bash
git clone https://github.com/alexhuhter313-debug/aegisq-miniapp
cd aegisq-miniapp
docker compose up -d
```

## Architecture

- **Frontend**: Telegram Mini App (HTML/JS) - dashboard, scanner, logs, config
- **Backend**: FastAPI + WebSocket - REST API for modules, real-time alerts
- **Bot**: Telegram bot bridge - Mini App auth, /commands, push alerts
- **Docker**: 24/7 auto-restart, zero maintenance

## Connect to Telegram

1. Create a bot via @BotFather
2. Set Mini App URL to your server: `https://your-server.com`
3. Set BOT_TOKEN env var
4. Deploy and go

## Connect to shadow313

Replace the mock modules in `backend/main.py` with real imports from your shadow313/AEGISQ stack.
