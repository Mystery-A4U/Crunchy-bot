# 🎌 CrunchyBot

Telegram bot that downloads Crunchyroll anime — Railway-ready, clean UI, premium tier system.

## Quick Deploy to Railway

1. Fork / push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables from `.env.example` in **Service → Variables**
4. Railway auto-builds via `Dockerfile` — done ✅

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TG_API_ID` | Telegram API ID | *required* |
| `TG_API_HASH` | Telegram API Hash | *required* |
| `TG_BOT_TOKEN` | Bot Token from @BotFather | *required* |
| `CR_EMAIL` | Crunchyroll account email | — |
| `CR_PASSWORD` | Crunchyroll account password | — |
| `CR_USE_ACCOUNT` | Use CR account (true/false) | `true` |
| `SUDO_USERS` | Comma-separated sudo user IDs | — |
| `PREMIUM_USERS` | Comma-separated premium user IDs | — |
| `AUTHORIZED_USERS` | Who can use the bot (empty = everyone) | — |
| `REGULAR_AUDIO_LIMIT` | Max audio tracks for regular users | `2` |
| `REGULAR_VIDEO_LIMIT_P` | Max video quality for regular users | `480` |
| `ENCODING_MODE` | `lossy` / `lossless` / `custom` | `lossy` |
| `USE_WATERMARK` | Add watermark to video | `true` |
| `WATERMARK_NAME` | Watermark text | `CrunchyBot` |
| `OUTPUT_FORMAT` | `mkv` or `mp4` | `mkv` |

See `.env.example` for the full list.

## User Tiers

| Tier | Quality | Audio Tracks | How to grant |
|------|---------|--------------|--------------|
| 👤 Regular | 480p max | 2 max | Default |
| ⭐ Premium | 1080p max | Unlimited | `/addpremium <id>` |
| 🔑 Sudo | Unlimited | Unlimited | Set `SUDO_USERS` env var |

## Bot Commands

```
/start        — Welcome screen + your tier
/help         — Full command reference
/dl <url>     — Download episode or series URL
/dl <title>   — Search by anime name
/cancel       — Cancel active session
/mystatus     — See your tier & limits

# Sudo only
/addpremium <id>   /rempremium <id>   /listpremium
/addsudo <id>      /remsudo <id>      /listsudo
```
