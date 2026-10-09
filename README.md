# AEGISQ Mini App

Telegram Mini App dashboard for the AEGISQ threat detection platform.

## Architecture

```
aegisq-miniapp/
├── frontend/index.html   # Telegram Mini App UI
├── backend/main.py       # FastAPI proxy + WebSocket
├── bot/bot.py            # Telegram bot bridge
├── Dockerfile            # Multi-stage container
└── docker-compose.yml    # Single service
```

## Quick Start

```bash
# Set your bot token
export BOT_TOKEN="your_telegram_bot_token"
export ALLOWED_USER_ID="your_telegram_id"

docker compose up -d --build
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `:80` | Telegram Mini App (frontend) |
| `:8001` | Backend API (proxies to detector) |
| `/api/detector/report` | Latest detection report |
| `/api/detector/detect` | Run detection |
| `/api/ws` | WebSocket for real-time updates |
