import os
import sys
import time
import json
import sqlite3
import uuid
import urllib.parse
import requests
import jwt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "8962868813:AAHQ41Up7TFKSJMeLk4Ao1O6c-9SY9Wq6ho"
DB_PATH = "/home/vallencia/.9router/db/data.sqlite"
JWT_SECRET_PATH = "/home/vallencia/.9router/jwt-secret"
BASE_URL = "http://127.0.0.1:20128"
OPENCODE_CONFIG_PATH = "/home/vallencia/.config/opencode/opencode.json"

# Conversation States
ADD_NAME, ADD_KEY, ADD_URL, ADD_OAUTH_CALLBACK = range(4)

def get_auth_token():
    try:
        with open(JWT_SECRET_PATH, "r") as f:
            secret = f.read().strip()
        payload = {
            "sub": "admin",
            "role": "admin",
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400
        }
        return jwt.encode(payload, secret, algorithm="HS256")
    except Exception as e:
        print(f"Error generating token: {e}")
        return None

def fetch_9router_stats():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    cookies = {"auth_token": token}
    
    api_stats = {}
    try:
        r = requests.get(f"{BASE_URL}/api/usage/stats?period=today", headers=headers, cookies=cookies, timeout=5)
        if r.status_code == 200:
            api_stats = r.json()
    except Exception as e:
        print(f"API fetch error: {e}")

    accounts = []
    daily_db = {}
    recent_logs = []
    settings_db = {}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT id, provider, name, email, isActive, priority, data FROM providerConnections ORDER BY priority ASC, id ASC")
        for r in c.fetchall():
            cid, prov, name, email, active, prio, data_raw = r
            d = {}
            try:
                d = json.loads(data_raw)
            except:
                pass
            accounts.append({
                "id": cid,
                "provider": prov,
                "email": email or name or "Unknown",
                "name": name or email or "Custom",
                "active": bool(active),
                "expiresAt": d.get("expiresAt"),
                "lastUsedAt": d.get("lastUsedAt"),
                "lastError": d.get("lastError"),
                "consecutiveUseCount": d.get("consecutiveUseCount", 0)
            })
            
        c.execute("SELECT dateKey, data FROM usageDaily ORDER BY dateKey DESC LIMIT 1")
        row = c.fetchone()
        if row:
            daily_db = json.loads(row[1])
            
        c.execute("SELECT timestamp, provider, model, connectionId, promptTokens, completionTokens, cost, status FROM usageHistory ORDER BY id DESC LIMIT 5")
        for r in c.fetchall():
            recent_logs.append({
                "time": r[0][11:19] if r[0] and len(r[0]) >= 19 else r[0],
                "model": r[2] or "unknown",
                "prompt": r[4] or 0,
                "comp": r[5] or 0,
                "cost": r[6] or 0.0,
                "status": r[7] or "ok"
            })
            
        c.execute("SELECT data FROM settings LIMIT 1")
        row_s = c.fetchone()
        if row_s:
            try:
                settings_db = json.loads(row_s[0])
            except:
                pass
                
        conn.close()
    except Exception as e:
        print(f"DB fetch error: {e}")
        
    return {
        "api": api_stats,
        "accounts": accounts,
        "daily": daily_db,
        "recent": recent_logs,
        "settings": settings_db
    }

def fetch_available_models_catalog(provider_filter="antigravity"):
    token = get_auth_token()
    cookies = {"auth_token": token}
    try:
        r = requests.get(f"{BASE_URL}/api/models", cookies=cookies, timeout=5)
        if r.status_code == 200:
            data = r.json()
            all_models = data.get("models", [])
            
            res = []
            for m in all_models:
                p = m.get("provider", "").lower()
                full_m = m.get("fullModel", "")
                
                if provider_filter == "antigravity":
                    if p in ["antigravity", "ag", "google", "gemini-cli"] or full_m.startswith("ag/"):
                        res.append(full_m)
                elif provider_filter == "all":
                    res.append(full_m)
                elif provider_filter in p:
                    res.append(full_m)
                    
            return sorted(list(set(res)))
    except Exception as e:
        print(f"Models catalog error: {e}")
    return []

def toggle_account_db(account_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT isActive, email, name FROM providerConnections WHERE id = ?", (account_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return False, "Akun tidak ditemukan"
        
        new_active = 0 if row[0] == 1 else 1
        c.execute("UPDATE providerConnections SET isActive = ? WHERE id = ?", (new_active, account_id))
        conn.commit()
        conn.close()
        name = row[1] or row[2] or account_id
        return True, f"Akun <code>{name}</code> berhasil di-{'AKTIFKAN' if new_active else 'NONAKTIFKAN'}!"
    except Exception as e:
        return False, str(e)

def delete_account_db(account_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT email, name FROM providerConnections WHERE id = ?", (account_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return False, "Akun tidak ditemukan"
        name = row[0] or row[1] or account_id
        c.execute("DELETE FROM providerConnections WHERE id = ?", (account_id,))
        conn.commit()
        conn.close()
        return True, f"🗑️ Akun <code>{name}</code> berhasil DIHAPUS dari 9Router!"
    except Exception as e:
        return False, str(e)

def set_round_robin_limit(limit_val):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT data FROM settings LIMIT 1")
        row = c.fetchone()
        data = json.loads(row[0]) if row else {}
        
        data["stickyRoundRobinLimit"] = limit_val
        if "providerStrategies" not in data:
            data["providerStrategies"] = {}
        if "antigravity" not in data["providerStrategies"]:
            data["providerStrategies"]["antigravity"] = {}
        data["providerStrategies"]["antigravity"]["stickyRoundRobinLimit"] = limit_val
        data["providerStrategies"]["antigravity"]["fallbackStrategy"] = "round-robin"
        
        c.execute("UPDATE settings SET data = ? WHERE id = 1", (json.dumps(data),))
        conn.commit()
        conn.close()
        return True, f"🎯 Sticky Round Robin Limit diubah ke: <b>{limit_val} request per akun</b>."
    except Exception as e:
        return False, str(e)

def add_custom_provider_db(provider_type, name, api_key, custom_url=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        new_id = str(uuid.uuid4())
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        
        data_payload = {
            "apiKey": api_key,
            "testStatus": "active",
            "lastUsedAt": None,
            "lastError": None
        }
        if custom_url:
            data_payload["baseUrl"] = custom_url
            
        c.execute("""
            INSERT INTO providerConnections (id, provider, authType, name, email, priority, isActive, data, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (new_id, provider_type, "apiKey", name, name, 1, 1, json.dumps(data_payload), now_iso, now_iso))
        
        conn.commit()
        conn.close()
        return True, f"✅ Provider <b>{name}</b> ({provider_type}) berhasil ditambahkan!"
    except Exception as e:
        return False, f"Gagal menambahkan provider: {e}"

def exchange_oauth_antigravity(callback_url_or_code, session_auth_data):
    token = get_auth_token()
    cookies = {"auth_token": token}
    headers = {"Content-Type": "application/json"}
    
    input_str = callback_url_or_code.strip()
    code = input_str
    url_state = None
    
    if "code=" in input_str or "http" in input_str:
        try:
            parsed = urllib.parse.urlparse(input_str)
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                code = params["code"][0]
            if "state" in params:
                url_state = params["state"][0]
        except Exception as e:
            print("URL parse error:", e)
            
    code_verifier = session_auth_data.get("codeVerifier")
    state = url_state or session_auth_data.get("state")
    redirect_uri = session_auth_data.get("redirectUri") or "http://localhost:8080/callback"
    
    payload = {
        "code": code,
        "redirectUri": redirect_uri,
        "codeVerifier": code_verifier,
        "state": state
    }
    
    try:
        r = requests.post(f"{BASE_URL}/api/oauth/antigravity/exchange", json=payload, cookies=cookies, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            email = data.get("email") or data.get("displayName") or "Google Account"
            return True, f"🎉 <b>Akun Antigravity Berhasil Terhubung!</b>\n\nEmail: <code>{email}</code>\nStatus: 🟢 <b>Active di Pool Round-Robin 9Router</b>"
        else:
            return False, f"Gagal exchange token (HTTP {r.status_code}): {r.text[:250]}"
    except Exception as e:
        return False, f"Error exchange: {e}"

def get_opencode_config_details():
    try:
        if os.path.exists(OPENCODE_CONFIG_PATH):
            with open(OPENCODE_CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            models = cfg.get("provider", {}).get("9router", {}).get("models", {})
            main_model = cfg.get("model", "")
            subagent_model = cfg.get("agent", {}).get("explorer", {}).get("model", "")
            return {
                "models": list(models.keys()),
                "main_model": main_model,
                "subagent_model": subagent_model
            }
    except Exception as e:
        print("Opencode read error:", e)
    return {"models": [], "main_model": "", "subagent_model": ""}

def set_opencode_main_model_file(model_name):
    try:
        if os.path.exists(OPENCODE_CONFIG_PATH):
            with open(OPENCODE_CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            
            clean_name = model_name if model_name.startswith("9router/") else f"9router/{model_name}"
            cfg["model"] = clean_name
            
            with open(OPENCODE_CONFIG_PATH, "w") as f:
                json.dump(cfg, f, indent=2)
            return True, f"⭐ Main Model Opencode diubah menjadi: <code>{clean_name}</code>!"
    except Exception as e:
        return False, str(e)
    return False, "Config tidak ditemukan."

def add_opencode_model_file(model_name):
    try:
        if os.path.exists(OPENCODE_CONFIG_PATH):
            with open(OPENCODE_CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            if "provider" not in cfg:
                cfg["provider"] = {}
            if "9router" not in cfg["provider"]:
                cfg["provider"]["9router"] = {"npm": "@ai-sdk/openai-compatible", "options": {"baseURL": "http://127.0.0.1:20128/v1", "apiKey": "sk-9router-local"}, "models": {}}
            if "models" not in cfg["provider"]["9router"]:
                cfg["provider"]["9router"]["models"] = {}
                
            cfg["provider"]["9router"]["models"][model_name] = {
                "name": model_name,
                "modalities": {
                    "input": ["text", "image"],
                    "output": ["text"]
                }
            }
            with open(OPENCODE_CONFIG_PATH, "w") as f:
                json.dump(cfg, f, indent=2)
            return True, f"✅ Model <code>{model_name}</code> berhasil ditambahkan ke Opencode!"
    except Exception as e:
        return False, f"Gagal update config: {e}"
    return False, "Config opencode.json tidak ditemukan."

def delete_opencode_model_file(model_name):
    try:
        if os.path.exists(OPENCODE_CONFIG_PATH):
            with open(OPENCODE_CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            models = cfg.get("provider", {}).get("9router", {}).get("models", {})
            if model_name in models:
                del models[model_name]
                with open(OPENCODE_CONFIG_PATH, "w") as f:
                    json.dump(cfg, f, indent=2)
                return True, f"🗑️ Model <code>{model_name}</code> berhasil dihapus dari Opencode!"
    except Exception as e:
        return False, str(e)
    return False, "Model tidak ditemukan."

def format_quota_report(data):
    api = data.get("api", {})
    daily = data.get("daily", {})
    accounts = data.get("accounts", [])
    settings = data.get("settings", {})
    
    total_req = api.get("totalRequests") or daily.get("requests") or 0
    prompt_tokens = (api.get("totalPromptTokens") or daily.get("promptTokens") or 0) / 1_000_000
    comp_tokens = (api.get("totalCompletionTokens") or daily.get("completionTokens") or 0) / 1_000
    cached_tokens = (api.get("totalCachedTokens") or 0) / 1_000_000
    cost = api.get("totalCost") or daily.get("cost") or 0.0
    
    rr_limit = settings.get("stickyRoundRobinLimit", 3)
    
    cache_pct = (cached_tokens / prompt_tokens * 100) if prompt_tokens > 0 else 0
    bar_len = 16
    filled = int(bar_len * (cache_pct / 100))
    bar = "▓" * filled + "░" * (bar_len - filled)
    
    text = "⚡ <b>9ROUTER COMMAND HUB (REALTIME)</b> ⚡\n"
    text += f"📅 <i>Sync: {time.strftime('%H:%M:%S')} UTC • Round-Robin: {rr_limit}x</i>\n\n"
    
    text += "┌───────────────────────────────────┐\n"
    text += f"│ 🚀 <b>TOTAL USAGE (24H)</b>\n"
    text += "├───────────────────────────────────┤\n"
    text += f"│ • Total Requests : <b>{total_req:,}x</b>\n"
    text += f"│ • Prompt Tokens  : <b>{prompt_tokens:.2f} M</b>\n"
    text += f"│ • Cached Tokens  : <b>{cached_tokens:.2f} M ({cache_pct:.1f}%)</b> ⚡\n"
    text += f"│ • Comp. Tokens   : <b>{comp_tokens:.2f} K</b>\n"
    text += f"│ • Total Cost     : <b>${cost:.4f}</b>\n"
    text += "└───────────────────────────────────┘\n\n"
    
    text += f"📈 <b>CACHE SAVINGS</b>: [{bar}] <b>{cache_pct:.1f}%</b>\n\n"
    
    text += "👥 <b>PROVIDER CONNECTIONS POOL</b>\n"
    for idx, acc in enumerate(accounts, 1):
        status_dot = "🟢" if acc["active"] else "🔴"
        last_used = acc["lastUsedAt"][11:19] if acc.get("lastUsedAt") else "-"
        text += f"{idx}. {status_dot} <b>[{acc['provider'].upper()}]</b> <code>{acc['email']}</code>\n"
        text += f"   └ Status: <b>{'Active' if acc['active'] else 'OFF'}</b> | Last: <code>{last_used} UTC</code>\n"
        
    return text

def format_account_detailed_quota(data, target_email=None):
    api = data.get("api", {})
    by_account = api.get("byAccount", {})
    accounts = data.get("accounts", [])
    
    text = "🔍 <b>DETAIL QUOTA & TOKEN PER AKUN (24H)</b>\n\n"
    
    acc_map = {}
    for k, v in by_account.items():
        email = v.get("accountName") or "Unknown"
        if email not in acc_map:
            acc_map[email] = {
                "requests": 0,
                "promptTokens": 0,
                "cachedTokens": 0,
                "completionTokens": 0,
                "cost": 0.0,
                "models": []
            }
        acc_map[email]["requests"] += v.get("requests", 0)
        acc_map[email]["promptTokens"] += v.get("promptTokens", 0)
        acc_map[email]["cachedTokens"] += v.get("cachedTokens", 0)
        acc_map[email]["completionTokens"] += v.get("completionTokens", 0)
        acc_map[email]["cost"] += v.get("cost", 0.0)
        acc_map[email]["models"].append({
            "model": v.get("rawModel"),
            "reqs": v.get("requests", 0),
            "cost": v.get("cost", 0.0)
        })
        
    if target_email:
        acc_info = acc_map.get(target_email)
        conn_info = next((a for a in accounts if a["email"] == target_email), None)
        status_str = "🟢 ACTIVE (In Pool)" if (conn_info and conn_info["active"]) else "🔴 OFF"
        
        text += f"👤 <b>Akun:</b> <code>{target_email}</code>\n"
        text += f"• Status Pool: {status_str}\n\n"
        
        if acc_info:
            p_m = acc_info["promptTokens"] / 1_000_000
            c_m = acc_info["cachedTokens"] / 1_000_000
            comp_k = acc_info["completionTokens"] / 1_000
            c_pct = (c_m / p_m * 100) if p_m > 0 else 0
            
            text += f"📊 <b>Statistik Token:</b>\n"
            text += f" • Requests Total  : <b>{acc_info['requests']:,}x</b>\n"
            text += f" • Prompt Ingested : <b>{p_m:.2f} M</b>\n"
            text += f" • Cached (Free)   : <b>{c_m:.2f} M ({c_pct:.1f}%)</b> ⚡\n"
            text += f" • Completion Out  : <b>{comp_k:.2f} K</b>\n"
            text += f" • Total Cost      : <b>${acc_info['cost']:.4f}</b>\n\n"
            
            text += f"🧠 <b>Model yang Dipakai:</b>\n"
            for m in acc_info["models"]:
                text += f" └ <code>{m['model']}</code> : <b>{m['reqs']}x</b> (${m['cost']:.4f})\n"
        else:
            text += "<i>Belum ada riwayat request untuk akun ini hari ini.</i>\n"
        return text

    # List all
    for idx, (email, st) in enumerate(acc_map.items(), 1):
        p_m = st["promptTokens"] / 1_000_000
        text += f"{idx}. 🟢 <code>{email}</code>\n"
        text += f"   • Requests : <b>{st['requests']}x</b> | Tokens: <b>{p_m:.2f}M</b>\n"
        text += f"   • Cost     : <b>${st['cost']:.4f}</b>\n\n"
        
    return text

def format_recent_logs(data):
    recent = data.get("recent", [])
    text = "📋 <b>RECENT REQUESTS LOGS (REALTIME)</b>\n\n"
    if not recent:
        return text + "<i>Belum ada request tercatat.</i>"
        
    for r in recent:
        status_icon = "✅" if r["status"] == "ok" else "⚠️"
        p_k = r["prompt"] / 1000
        text += f"{status_icon} <b>[{r['time']}]</b> <code>{r['model']}</code>\n"
        text += f"   └ Tokens: <b>{p_k:.1f}k in / {r['comp']} out</b> | Cost: <b>${r['cost']:.5f}</b>\n"
    return text

def format_models_breakdown(data):
    daily = data.get("daily", {})
    by_model = daily.get("byModel", {})
    
    text = "🧠 <b>USAGE BREAKDOWN BY MODEL</b>\n\n"
    if not by_model:
        return text + "<i>Tidak ada data model hari ini.</i>"
        
    for model_key, stats in by_model.items():
        m_name = stats.get("rawModel") or model_key
        reqs = stats.get("requests", 0)
        p_m = stats.get("promptTokens", 0) / 1_000_000
        cost = stats.get("cost", 0.0)
        text += f"🔹 <b>{m_name}</b>\n"
        text += f"   • Requests : <b>{reqs}x</b>\n"
        text += f"   • Prompts  : <b>{p_m:.2f} M</b>\n"
        text += f"   • Cost     : <b>${cost:.4f}</b>\n\n"
    return text

async def safe_edit_message(query, text, reply_markup):
    try:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            pass
        else:
            raise e

def build_main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_quota"),
            InlineKeyboardButton("📋 Logs", callback_data="view_logs"),
            InlineKeyboardButton("🧠 Models", callback_data="view_models")
        ],
        [
            InlineKeyboardButton("📊 Detail Quota Akun", callback_data="detailed_quota_menu"),
            InlineKeyboardButton("⚙️ Kelola Akun & Hapus", callback_data="manage_accounts")
        ],
        [
            InlineKeyboardButton("🎯 Round Robin", callback_data="rr_menu"),
            InlineKeyboardButton("💻 Opencode CLI Manager", callback_data="cli_tools_menu")
        ],
        [
            InlineKeyboardButton("➕ Tambah Provider", callback_data="add_provider_menu")
        ]
    ])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = fetch_9router_stats()
    text = format_quota_report(data)
    reply_markup = build_main_keyboard()
    
    if update.message:
        await update.message.reply_html(text, reply_markup=reply_markup)
    elif update.callback_query:
        await safe_edit_message(update.callback_query, text, reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = fetch_9router_stats()
    
    if query.data in ["refresh_quota", "view_quota"]:
        text = format_quota_report(data)
        await safe_edit_message(query, text, build_main_keyboard())
        
    elif query.data == "view_logs":
        text = format_recent_logs(data)
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh Logs", callback_data="view_logs"),
                InlineKeyboardButton("⬅️ Menu Utama", callback_data="view_quota")
            ]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "view_models":
        text = format_models_breakdown(data)
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="view_models"),
                InlineKeyboardButton("⬅️ Menu Utama", callback_data="view_quota")
            ]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "detailed_quota_menu":
        accounts = data.get("accounts", [])
        text = "📊 <b>DETAIL PENGGUNAAN & KUOTA PER AKUN</b>\n\n"
        text += "Pilih salah satu akun di bawah untuk melihat rincian token & sisa kuotanya:\n\n"
        
        keyboard = []
        for acc in accounts:
            label = f"👤 {acc['email']}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"show_acc_quota_{acc['email']}")])
            
        keyboard.append([InlineKeyboardButton("⬅️ Menu Utama", callback_data="view_quota")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("show_acc_quota_"):
        email = query.data.replace("show_acc_quota_", "")
        text = format_account_detailed_quota(data, target_email=email)
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data=f"show_acc_quota_{email}")],
            [InlineKeyboardButton("⬅️ Pilih Akun Lain", callback_data="detailed_quota_menu")],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data="view_quota")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "manage_accounts":
        accounts = data.get("accounts", [])
        text = "⚙️ <b>KELOLA AKUN & PROVIDER</b>\n\n"
        text += "Pilih akun di bawah untuk mengubah status (ON/OFF) atau menghapus akun:\n\n"
        
        keyboard = []
        for acc in accounts:
            status_emoji = "🟢" if acc["active"] else "🔴"
            label = f"{status_emoji} [{acc['provider']}] {acc['email'][:18]}"
            keyboard.append([
                InlineKeyboardButton(label, callback_data=f"acc_detail_{acc['id']}")
            ])
            
        keyboard.append([InlineKeyboardButton("⬅️ Menu Utama", callback_data="view_quota")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("acc_detail_"):
        acc_id = query.data.replace("acc_detail_", "")
        accounts = data.get("accounts", [])
        acc = next((a for a in accounts if a["id"] == acc_id), None)
        if not acc:
            await query.answer("Akun tidak ditemukan")
            return
            
        status_text = "🟢 AKTIF" if acc["active"] else "🔴 NONAKTIF"
        toggle_label = "🔴 Matikan Akun" if acc["active"] else "🟢 Aktifkan Akun"
        
        text = f"👤 <b>DETAIL AKUN:</b>\n\n"
        text += f"• <b>Email/Label</b>: <code>{acc['email']}</code>\n"
        text += f"• <b>Provider</b>: <code>{acc['provider'].upper()}</code>\n"
        text += f"• <b>Status</b>: {status_text}\n"
        text += f"• <b>ID</b>: <code>{acc['id']}</code>\n\n"
        text += "<i>Pilih tindakan di bawah:</i>"
        
        keyboard = [
            [InlineKeyboardButton(toggle_label, callback_data=f"toggle_{acc['id']}")],
            [InlineKeyboardButton("📊 Cek Detail Kuota", callback_data=f"show_acc_quota_{acc['email']}")],
            [InlineKeyboardButton("🗑️ Hapus Akun Ini", callback_data=f"del_confirm_{acc['id']}")],
            [InlineKeyboardButton("⬅️ Kembali ke Daftar", callback_data="manage_accounts")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("toggle_"):
        acc_id = query.data.replace("toggle_", "")
        ok, msg = toggle_account_db(acc_id)
        await query.answer(msg)
        
        data = fetch_9router_stats()
        accounts = data.get("accounts", [])
        acc = next((a for a in accounts if a["id"] == acc_id), None)
        if acc:
            status_text = "🟢 AKTIF" if acc["active"] else "🔴 NONAKTIF"
            toggle_label = "🔴 Matikan Akun" if acc["active"] else "🟢 Aktifkan Akun"
            text = f"👤 <b>DETAIL AKUN:</b>\n\n{msg}\n\n"
            text += f"• <b>Email/Label</b>: <code>{acc['email']}</code>\n"
            text += f"• <b>Provider</b>: <code>{acc['provider'].upper()}</code>\n"
            text += f"• <b>Status</b>: {status_text}\n\n"
            keyboard = [
                [InlineKeyboardButton(toggle_label, callback_data=f"toggle_{acc['id']}")],
                [InlineKeyboardButton("📊 Cek Detail Kuota", callback_data=f"show_acc_quota_{acc['email']}")],
                [InlineKeyboardButton("🗑️ Hapus Akun Ini", callback_data=f"del_confirm_{acc['id']}")],
                [InlineKeyboardButton("⬅️ Kembali ke Daftar", callback_data="manage_accounts")]
            ]
            await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
            
    elif query.data.startswith("del_confirm_"):
        acc_id = query.data.replace("del_confirm_", "")
        accounts = data.get("accounts", [])
        acc = next((a for a in accounts if a["id"] == acc_id), None)
        name = acc["email"] if acc else acc_id
        
        text = f"⚠️ <b>KONFIRMASI HAPUS AKUN</b>\n\n"
        text += f"Apakah kamu yakin ingin menghapus akun <code>{name}</code> dari 9Router?\n"
        text += "<i>Tindakan ini tidak dapat dibatalkan.</i>"
        
        keyboard = [
            [InlineKeyboardButton("🔥 Ya, Hapus Sekarang", callback_data=f"del_do_{acc_id}")],
            [InlineKeyboardButton("❌ Batal", callback_data=f"acc_detail_{acc_id}")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("del_do_"):
        acc_id = query.data.replace("del_do_", "")
        ok, msg = delete_account_db(acc_id)
        await query.answer(msg)
        
        text = f"{msg}\n\nKetik /quota untuk melihat status pool terbaru."
        keyboard = [[InlineKeyboardButton("⬅️ Kembali ke Daftar Akun", callback_data="manage_accounts")]]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "rr_menu":
        settings = data.get("settings", {})
        cur_limit = settings.get("stickyRoundRobinLimit", 3)
        
        text = "🎯 <b>PENGATURAN ROTASI ROUND-ROBIN</b>\n\n"
        text += f"• <b>Sticky Limit Saat Ini</b>: <b>{cur_limit}x request berturut-turut per akun</b>\n"
        text += "• <b>Strategi</b>: Round-Robin Seimbang antar seluruh akun Google Antigravity aktif.\n\n"
        text += "<i>Pilih batas request sebelum berpindah ke akun berikutnya:</i>"
        
        keyboard = [
            [
                InlineKeyboardButton("1x (Ganti Tiap Request)", callback_data="set_rr_1"),
                InlineKeyboardButton("2x", callback_data="set_rr_2"),
                InlineKeyboardButton("3x (Default)", callback_data="set_rr_3")
            ],
            [
                InlineKeyboardButton("5x", callback_data="set_rr_5"),
                InlineKeyboardButton("10x", callback_data="set_rr_10")
            ],
            [InlineKeyboardButton("⬅️ Menu Utama", callback_data="view_quota")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("set_rr_"):
        val = int(query.data.replace("set_rr_", ""))
        ok, msg = set_round_robin_limit(val)
        await query.answer(msg)
        
        text = f"🎯 <b>PENGATURAN ROTASI ROUND-ROBIN</b>\n\n{msg}\n\n<i>Pilih batas baru jika ingin mengubah lagi:</i>"
        keyboard = [
            [
                InlineKeyboardButton("1x", callback_data="set_rr_1"),
                InlineKeyboardButton("2x", callback_data="set_rr_2"),
                InlineKeyboardButton("3x", callback_data="set_rr_3"),
                InlineKeyboardButton("5x", callback_data="set_rr_5"),
                InlineKeyboardButton("10x", callback_data="set_rr_10")
            ],
            [InlineKeyboardButton("⬅️ Menu Utama", callback_data="view_quota")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "cli_tools_menu":
        opencode_info = get_opencode_config_details()
        models = opencode_info["models"]
        main_m = opencode_info["main_model"]
        
        text = "💻 <b>OPENCODE CLI MODEL & CONFIG MANAGER</b>\n\n"
        text += f"⭐ <b>Main / Default Model Saat Ini:</b>\n👉 <code>{main_m}</code>\n\n"
        text += f"📦 <b>Daftar Model Tersedia di Opencode ({len(models)}):</b>\n"
        for m in models:
            is_active_main = (m == main_m or f"9router/{m}" == main_m)
            prefix = "⭐ [MAIN] " if is_active_main else "• "
            text += f"{prefix}<code>{m}</code>\n"
            
        text += "\n<i>Pilih menu di bawah:</i>"
        keyboard = [
            [InlineKeyboardButton("⭐ Set Default / Main Model", callback_data="opencode_set_main_menu")],
            [InlineKeyboardButton("📥 Tambah Model dari Katalog 9Router", callback_data="pick_catalog_models_0")],
            [InlineKeyboardButton("🗑️ Hapus Model dari Opencode", callback_data="opencode_del_list")],
            [InlineKeyboardButton("⬅️ Menu Utama", callback_data="view_quota")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "opencode_set_main_menu":
        opencode_info = get_opencode_config_details()
        models = opencode_info["models"]
        main_m = opencode_info["main_model"]
        
        text = "⭐ <b>PILIH MAIN / DEFAULT MODEL UNTUK OPENCODE</b>\n\n"
        text += f"Main model saat ini: <code>{main_m}</code>\n\n"
        text += "<i>Klik salah satu model di bawah untuk menjadikannya model utama:</i>\n\n"
        
        keyboard = []
        for m in models:
            is_active_main = (m == main_m or f"9router/{m}" == main_m)
            tag = "✅ " if is_active_main else "🔹 "
            keyboard.append([
                InlineKeyboardButton(f"{tag}{m}", callback_data=f"set_opencode_main_{m[:30]}")
            ])
            
        keyboard.append([InlineKeyboardButton("⬅️ Kembali ke CLI Tools", callback_data="cli_tools_menu")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("set_opencode_main_"):
        target_short = query.data.replace("set_opencode_main_", "")
        opencode_info = get_opencode_config_details()
        full_model = next((m for m in opencode_info["models"] if m.startswith(target_short)), target_short)
        
        ok, msg = set_opencode_main_model_file(full_model)
        await query.answer("Main model berhasil diubah!")
        
        opencode_info = get_opencode_config_details()
        text = f"⭐ <b>MAIN MODEL BERHASIL DIUBAH</b>\n\n{msg}\n\nSekarang Opencode CLI otomatis memakai model ini secara default."
        keyboard = [
            [InlineKeyboardButton("💻 Kembali ke Opencode Manager", callback_data="cli_tools_menu")],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data="view_quota")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("pick_catalog_models_"):
        page = int(query.data.replace("pick_catalog_models_", ""))
        catalog = fetch_available_models_catalog("antigravity")
        active_opencode = set(get_opencode_config_details()["models"])
        
        per_page = 6
        total_pages = (len(catalog) + per_page - 1) // per_page
        start_idx = page * per_page
        cur_items = catalog[start_idx:start_idx + per_page]
        
        text = f"📥 <b>PILIH MODEL DARI KATALOG 9ROUTER (Hal {page+1}/{total_pages})</b>\n\n"
        text += "Klik tombol model di bawah untuk <b>LANGSUNG MENAMBAHKAN</b> ke Opencode CLI:\n\n"
        
        keyboard = []
        for m in cur_items:
            is_added = m in active_opencode
            status_tag = "✅ (Aktif)" if is_added else "➕ Tambah"
            keyboard.append([
                InlineKeyboardButton(f"{status_tag} {m}", callback_data=f"btn_add_model_{m}")
            ])
            
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"pick_catalog_models_{page-1}"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"pick_catalog_models_{page+1}"))
            
        if nav_row:
            keyboard.append(nav_row)
        keyboard.append([InlineKeyboardButton("⬅️ Kembali ke CLI Tools", callback_data="cli_tools_menu")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("btn_add_model_"):
        model_to_add = query.data.replace("btn_add_model_", "")
        ok, msg = add_opencode_model_file(model_to_add)
        await query.answer(f"{model_to_add} ditambahkan!")
        
        catalog = fetch_available_models_catalog("antigravity")
        active_opencode = set(get_opencode_config_details()["models"])
        page = 0
        per_page = 6
        total_pages = (len(catalog) + per_page - 1) // per_page
        cur_items = catalog[:per_page]
        
        text = f"📥 <b>PILIH MODEL DARI KATALOG 9ROUTER</b>\n\n{msg}\n\n"
        keyboard = []
        for m in cur_items:
            is_added = m in active_opencode
            status_tag = "✅ (Aktif)" if is_added else "➕ Tambah"
            keyboard.append([
                InlineKeyboardButton(f"{status_tag} {m}", callback_data=f"btn_add_model_{m}")
            ])
            
        if total_pages > 1:
            keyboard.append([InlineKeyboardButton("Next ➡️", callback_data="pick_catalog_models_1")])
        keyboard.append([InlineKeyboardButton("⬅️ Kembali ke CLI Tools", callback_data="cli_tools_menu")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "opencode_del_list":
        models = get_opencode_config_details()["models"]
        text = "🗑️ <b>HAPUS MODEL DARI OPENCODE</b>\n\nKlik nama model di bawah untuk menghapusnya:\n\n"
        keyboard = []
        for m in models:
            keyboard.append([InlineKeyboardButton(f"❌ {m}", callback_data=f"del_opencode_{m[:30]}")])
        keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="cli_tools_menu")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("del_opencode_"):
        m_name = query.data.replace("del_opencode_", "")
        models = get_opencode_config_details()["models"]
        full_m = next((m for m in models if m.startswith(m_name)), m_name)
        ok, msg = delete_opencode_model_file(full_m)
        await query.answer(msg)
        
        models = get_opencode_config_details()["models"]
        text = f"🗑️ <b>HAPUS MODEL DARI OPENCODE</b>\n\n{msg}\n\n"
        keyboard = []
        for m in models:
            keyboard.append([InlineKeyboardButton(f"❌ {m}", callback_data=f"del_opencode_{m[:30]}")])
        keyboard.append([InlineKeyboardButton("⬅️ Kembali ke CLI Tools", callback_data="cli_tools_menu")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "add_provider_menu":
        text = "➕ <b>PILIH TIPE PROVIDER UNTUK DITAMBAHKAN</b>\n\n"
        text += "Pilih provider AI yang ingin kamu masukkan ke 9router:\n\n"
        text += "1. <b>Google Antigravity (Gemini / Claude Free Pool)</b>\n"
        text += "2. <b>Groq / DeepSeek / OpenAI / OpenRouter</b> (API Key)\n"
        text += "3. <b>Custom OpenAI Compatible</b> (Key + Custom URL)\n"
        
        keyboard = [
            [InlineKeyboardButton("🚀 Google Antigravity (OAuth)", callback_data="prov_type_antigravity")],
            [InlineKeyboardButton("🟣 Groq API", callback_data="prov_type_groq"), InlineKeyboardButton("🔵 DeepSeek API", callback_data="prov_type_deepseek")],
            [InlineKeyboardButton("🟢 OpenAI API", callback_data="prov_type_openai"), InlineKeyboardButton("🟠 OpenRouter", callback_data="prov_type_openrouter")],
            [InlineKeyboardButton("🌐 Custom OpenAI-Compatible", callback_data="prov_type_custom")],
            [InlineKeyboardButton("⬅️ Menu Utama", callback_data="view_quota")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))

# Add Provider Wizard Handlers
async def start_add_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    prov_type = query.data.replace("prov_type_", "")
    context.user_data["prov_type"] = prov_type
    
    if prov_type == "antigravity":
        token = get_auth_token()
        cookies = {"auth_token": token}
        try:
            r = requests.get(f"{BASE_URL}/api/oauth/antigravity/authorize", cookies=cookies, timeout=5)
            auth_data = r.json()
            auth_url = auth_data.get("authUrl")
            
            context.user_data["oauth_data"] = auth_data
            
            text = "🚀 <b>TAMBAH AKUN GOOGLE ANTIGRAVITY</b>\n\n"
            text += "1. Buka tautan Google OAuth di bawah di browser kamu:\n"
            text += f"👉 <a href=\"{auth_url}\"><b>KLIK DI SINI UNTUK LOGIN GOOGLE</b></a>\n\n"
            text += "2. Pilih akun Google baru kamu & klik <b>Allow / Izinkan</b>.\n\n"
            text += "3. Browser akan mengarah ke <code>http://localhost:8080/callback?code=...</code> (salin URL lengkap dari address bar browser kamu).\n\n"
            text += "4. <b>Kirimkan (paste) link lengkap / kode callback tersebut ke chat ini</b>:\n\n"
            text += "<i>Ketik /cancel untuk membatalkan.</i>"
            
            await safe_edit_message(query, text, None)
            return ADD_OAUTH_CALLBACK
        except Exception as e:
            await query.edit_message_text(f"❌ Gagal membuat URL OAuth: {e}")
            return ConversationHandler.END
            
    text = f"📝 <b>Tambah Provider [{prov_type.upper()}]</b>\n\n"
    text += "Masukkan <b>Nama Label</b> untuk akun/provider ini (contoh: <code>Akun Utama</code>):\n\n"
    text += "<i>Ketik /cancel untuk membatalkan.</i>"
    
    await safe_edit_message(query, text, None)
    return ADD_NAME

async def wizard_oauth_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    session_auth_data = context.user_data.get("oauth_data", {})
    
    await update.message.reply_text("⏳ Sedang memproses token Google Antigravity...")
    ok, msg = exchange_oauth_antigravity(user_input, session_auth_data)
    
    keyboard = [[InlineKeyboardButton("📊 Lihat Dashboard Quota", callback_data="view_quota")]]
    await update.message.reply_html(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def wizard_name_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["prov_name"] = name
    prov_type = context.user_data.get("prov_type")
    
    text = f"🔑 Masukkan <b>API Key</b> untuk <b>{name}</b> ({prov_type.upper()}):\n\n"
    text += "<i>API Key akan disimpan terenkripsi di database 9Router lokal.</i>"
    
    await update.message.reply_html(text)
    return ADD_KEY

async def wizard_key_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = update.message.text.strip()
    context.user_data["prov_key"] = api_key
    prov_type = context.user_data.get("prov_type")
    name = context.user_data.get("prov_name")
    
    if prov_type == "custom":
        text = f"🌐 Masukkan <b>Base URL Endpoint</b> (contoh: <code>https://api.together.xyz/v1</code>):\n"
        await update.message.reply_html(text)
        return ADD_URL
    else:
        ok, msg = add_custom_provider_db(prov_type, name, api_key)
        keyboard = [[InlineKeyboardButton("📊 Lihat Dashboard Quota", callback_data="view_quota")]]
        await update.message.reply_html(f"{msg}\n\nSekarang model dari provider ini langsung aktif di 9Router!", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

async def wizard_url_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    custom_url = update.message.text.strip()
    api_key = context.user_data.get("prov_key")
    name = context.user_data.get("prov_name")
    prov_type = context.user_data.get("prov_type")
    
    ok, msg = add_custom_provider_db(prov_type, name, api_key, custom_url)
    keyboard = [[InlineKeyboardButton("📊 Lihat Dashboard Quota", callback_data="view_quota")]]
    await update.message.reply_html(f"{msg}\n\nEndpoint custom langsung terhubung ke 9Router!", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def cancel_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Aksi dibatalkan. Ketik /quota untuk kembali.")
    return ConversationHandler.END

def main():
    print("Starting 9Router Complete Manager Bot with Set Main Model & Detailed Per-Account Quota...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    wizard_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_add_wizard, pattern="^prov_type_")
        ],
        states={
            ADD_OAUTH_CALLBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, wizard_oauth_step)],
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, wizard_name_step)],
            ADD_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, wizard_key_step)],
            ADD_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, wizard_url_step)],
        },
        fallbacks=[CommandHandler("cancel", cancel_wizard)],
    )
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("quota", start_command))
    app.add_handler(CommandHandler("token", start_command))
    app.add_handler(CommandHandler("usage", start_command))
    app.add_handler(wizard_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
