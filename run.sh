#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "⚡ [9Router Hub] Memeriksa environment..."

# 1. Deteksi Python & Package Manager (uv / pip)
if command -v uv &> /dev/null; then
    PY_RUNNER="uv"
elif command -v python3 &> /dev/null; then
    PY_RUNNER="python3"
else
    echo "❌ Error: Python3 tidak ditemukan di sistem!"
    exit 1
fi

# 2. Auto-create venv jika belum ada
if [ ! -d ".venv" ]; then
    echo "📦 Membuat virtual environment (.venv)..."
    if [ "$PY_RUNNER" = "uv" ]; then
        uv venv .venv
    else
        python3 -m venv .venv
    fi
fi

# 3. Auto-install dependencies jika belum lengkap
if [ ! -f ".venv/.deps_installed" ] || [ requirements.txt -nt .venv/.deps_installed ]; then
    echo "📦 Menyiapkan dependencies dari requirements.txt..."
    if [ "$PY_RUNNER" = "uv" ]; then
        uv pip install -r requirements.txt
    else
        .venv/bin/pip install -r requirements.txt
    fi
    touch .venv/.deps_installed
fi

# 4. Auto-detect path 9Router & OpenCode
DETECTED_DB=""
DETECTED_JWT=""
DETECTED_OPENCODE=""

for p in "$HOME/.9router/db/data.sqlite" "$HOME/.local/share/9router/db/data.sqlite"; do
    [ -f "$p" ] && DETECTED_DB="$p" && break
done

for p in "$HOME/.9router/jwt-secret" "$HOME/.local/share/9router/jwt-secret"; do
    [ -f "$p" ] && DETECTED_JWT="$p" && break
done

for p in "$HOME/.config/opencode/opencode.json" "$HOME/.opencode/opencode.json"; do
    [ -f "$p" ] && DETECTED_OPENCODE="$p" && break
done

# 5. Auto-config .env
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || touch .env
fi

if [ -n "$DETECTED_DB" ]; then
    grep -q "^ROUTER_DB_PATH=" .env && sed -i "s|^ROUTER_DB_PATH=.*|ROUTER_DB_PATH=$DETECTED_DB|" .env || echo "ROUTER_DB_PATH=$DETECTED_DB" >> .env
fi

if [ -n "$DETECTED_JWT" ]; then
    grep -q "^ROUTER_JWT_PATH=" .env && sed -i "s|^ROUTER_JWT_PATH=.*|ROUTER_JWT_PATH=$DETECTED_JWT|" .env || echo "ROUTER_JWT_PATH=$DETECTED_JWT" >> .env
fi

if [ -n "$DETECTED_OPENCODE" ]; then
    grep -q "^OPENCODE_CONFIG_PATH=" .env && sed -i "s|^OPENCODE_CONFIG_PATH=.*|OPENCODE_CONFIG_PATH=$DETECTED_OPENCODE|" .env || echo "OPENCODE_CONFIG_PATH=$DETECTED_OPENCODE" >> .env
fi

# 6. Cek & Tanya BOT_TOKEN jika belum ada
CURRENT_TOKEN=$(grep -E "^BOT_TOKEN=" .env 2>/dev/null | cut -d'=' -f2- | tr -d ' "')
if [ -z "$CURRENT_TOKEN" ] || [ "$CURRENT_TOKEN" = "YOUR_TELEGRAM_BOT_TOKEN" ]; then
    echo ""
    echo "🔑 Masukkan Telegram Bot Token kamu (dari @BotFather):"
    read -r USER_TOKEN
    if [ -n "$USER_TOKEN" ]; then
        sed -i "s|^BOT_TOKEN=.*|BOT_TOKEN=$USER_TOKEN|" .env
        echo "✓ Bot Token tersimpan!"
    else
        echo "❌ Bot Token wajib diisi untuk menjalankan bot."
        exit 1
    fi
fi

# 7. Langsung jalankan bot
source .venv/bin/activate
echo "🚀 9Router Telegram Bot siap dijalankan..."
exec python3 main.py
