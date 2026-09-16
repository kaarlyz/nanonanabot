<div align="center">

# ⚡ 9Router Telegram Command Hub

**Enterprise-grade Telegram bot for managing, monitoring, and orchestrating multi-account AI model gateways, load-balancing quotas, and OpenCode CLI runtime engines.**

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-v22.8-blue.svg)](https://python-telegram-bot.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active%20%26%20production%20ready-success.svg)]()

</div>

---

## 📌 Overview

**9Router Telegram Command Hub** transforms your Telegram into a fully-interactive DevOps dashboard for local & cloud AI proxy infrastructure. Directly query real-time token telemetry, manage Google Antigravity OAuth pools with PKCE, tune Sticky Round-Robin load balancers, and seamlessly configure primary models on OpenCode CLI via one-click catalog buttons.

---

## ✨ Key Capabilities

### 📊 Real-Time Telemetry & Quota Audit
- **Comprehensive 24H Overview**: Instant tracking of Total Requests, Prompt Token volume, Output Completion, Prompt Caching efficiency (%), and estimated financial costs ($).
- **Per-Account Token Breakdown**: View dedicated token consumption, cache hits, and model distribution per Google / custom provider account.
- **Live Transaction Logs**: Real-time audit trails with millisecond precision for every upstream model request.

### 👥 Provider Pool & Multi-Account Orchestration
- **Google Antigravity OAuth Relay**: Interactive PKCE authentication wizard inside chat. Authenticate multiple Google accounts into the round-robin pool without touching terminal commands.
- **API Key Providers**: Add Groq, DeepSeek, OpenAI, OpenRouter, and custom OpenAI-compatible endpoints with encrypted storage.
- **Account State & Lifecycle**: Toggle account status (🟢 Active / 🔴 Disabled) or permanently delete accounts with single-click inline confirmations.

### 🎯 Dynamic Load-Balancing & Routing
- **Sticky Round-Robin Tuner**: Adjust consecutive request quotas before switching pool connections (`1x`, `2x`, `3x`, `5x`, `10x`) live.
- **Zero Downtime**: Settings sync directly into 9Router SQLite database with immediate propagation.

### 💻 OpenCode CLI & Model Hub Integration
- **Interactive Catalog Browser**: Browse available models from 9Router (`gemini-3.7-flash`, `claude-3-7-sonnet`, `gemini-3.8-flash`, etc.) with paginated inline buttons.
- **One-Click Primary Model Selector**: Choose the primary default engine for OpenCode CLI without manually editing `~/.config/opencode/opencode.json`.
- **Model Registry Management**: Add and remove configured model declarations on the fly.

---

## 🏗️ Architecture & Project Structure

```text
bottele/
├── config/
│   ├── __init__.py
│   └── settings.py          # Environment variables & system configuration
├── core/
│   ├── __init__.py
│   └── keyboards.py         # Reusable Telegram InlineKeyboardMarkup builders
├── handlers/
│   ├── __init__.py
│   └── dashboard_handlers.py# Command, callback query, and wizard handlers
├── services/
│   ├── __init__.py
│   └── router_service.py    # 9Router REST API, SQLite queries & OpenCode engine
├── utils/
│   ├── __init__.py
│   └── formatter.py        # High-signal HTML typography & dashboard layouts
├── main.py                  # Main entry point & polling scheduler
├── requirements.txt         # Production dependencies
├── .env.example             # Example environment configuration
└── README.md                # Documentation
```

---

## 🚀 Quickstart & Installation

### Prerequisites
- Python 3.11+
- [9Router](https://github.com/9router/9router) running locally on port `20128`

### 1. Clone Repository & Install Dependencies
```bash
git clone https://github.com/kaarlyz/9router-telegram-hub.git
cd 9router-telegram-hub

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your Telegram Bot Token:
```bash
cp .env.example .env
```

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
ROUTER_BASE_URL=http://127.0.0.1:20128
ROUTER_DB_PATH=/home/username/.9router/db/data.sqlite
ROUTER_JWT_PATH=/home/username/.9router/jwt-secret
OPENCODE_CONFIG_PATH=/home/username/.config/opencode/opencode.json
```

### 3. Run the Bot
```bash
python main.py
```

---

## 📱 Bot Commands & Usage

| Command | Description |
| :--- | :--- |
| `/start` | Launch the main interactive 9Router dashboard |
| `/dashboard` | View telemetry metrics, cache savings, and connection health |
| `/quota` | Audit token quotas and balance distribution |
| `/token` | Detailed token statistics and cost breakdown |
| `/cancel` | Cancel active provider creation or configuration wizards |

---

## 🔒 Security & Privacy

- **PKCE Token Exchange**: Antigravity OAuth uses RFC 7636 PKCE with temporary code verifiers.
- **JWT Authorization**: Communicates with 9Router core using administrative HS256 JWT tokens.
- **Safe Secrets Handling**: API keys and OAuth tokens are stored in the local SQLite database and never logged in plain text.

---

## 📄 License
This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.
