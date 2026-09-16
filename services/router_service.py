import time
import json
import sqlite3
import uuid
import urllib.parse
import requests
import jwt
from config.settings import DB_PATH, JWT_SECRET_PATH, BASE_URL, OPENCODE_CONFIG_PATH

def get_auth_token():
    try:
        if not os.path.exists(JWT_SECRET_PATH):
            return None
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
        return True, f"Akun <code>{name}</code> status: <b>{'🟢 AKTIF' if new_active else '🔴 NONAKTIF'}</b>"
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
        return True, f"🗑️ Akun <code>{name}</code> berhasil dihapus permanen!"
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
        return True, f"🎯 Sticky Round-Robin diset ke: <b>{limit_val} request per akun</b>."
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
        return True, f"✅ Provider <b>{name}</b> ({provider_type.upper()}) berhasil ditambahkan ke 9Router!"
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
            return True, f"🎉 <b>Akun Antigravity Berhasil Terhubung!</b>\n\n• Email: <code>{email}</code>\n• Status: 🟢 <b>Active Pool</b>"
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
            return True, f"⭐ Main Model Opencode diset ke: <code>{clean_name}</code>!"
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
            return True, f"✅ Model <code>{model_name}</code> aktif di Opencode!"
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
                return True, f"🗑️ Model <code>{model_name}</code> dihapus dari Opencode!"
    except Exception as e:
        return False, str(e)
    return False, "Model tidak ditemukan."
