import time

def format_quota_report(data):
    api = data.get("api", {})
    daily = data.get("daily", {})
    accounts = data.get("accounts", [])
    settings = data.get("settings", {})
    period = data.get("period", "today").upper()
    
    total_req = api.get("totalRequests") or daily.get("requests") or 0
    prompt_tokens = (api.get("totalPromptTokens") or daily.get("promptTokens") or 0) / 1_000_000
    comp_tokens = (api.get("totalCompletionTokens") or daily.get("completionTokens") or 0) / 1_000
    cached_tokens = (api.get("totalCachedTokens") or 0) / 1_000_000
    cost = api.get("totalCost") or daily.get("cost") or 0.0
    
    rr_limit = settings.get("stickyRoundRobinLimit", 3)
    caveman_on = settings.get("cavemanEnabled", False)
    ponytail_on = settings.get("ponytailEnabled", False)
    
    cache_pct = (cached_tokens / prompt_tokens * 100) if prompt_tokens > 0 else 0
    bar_len = 12
    filled = int(bar_len * (cache_pct / 100))
    bar = "▓" * filled + "░" * (bar_len - filled)
    
    text = f"⚡ <b>9ROUTER INFRASTRUCTURE HUB</b> ⚡\n"
    text += f"<code>Timeframe : {period} ({time.strftime('%H:%M:%S')} UTC)</code>\n"
    text += f"<code>Balancer  : Round-Robin ({rr_limit}x sticky limit)</code>\n\n"
    
    text += "┌─────────────────────────────────────┐\n"
    text += f"│ 🚀 <b>TELEMETRY USAGE ({period})</b>\n"
    text += "├─────────────────────────────────────┤\n"
    text += f"│ • Total Requests : <b>{total_req:,}x</b>\n"
    text += f"│ • Prompt Ingest  : <b>{prompt_tokens:.2f} M</b>\n"
    text += f"│ • Cached (Free)  : <b>{cached_tokens:.2f} M ({cache_pct:.1f}%)</b> ⚡\n"
    text += f"│ • Completion Out : <b>{comp_tokens:.2f} K</b>\n"
    text += f"│ • Incurred Cost  : <b>${cost:.4f}</b>\n"
    text += "└─────────────────────────────────────┘\n\n"
    
    text += f"📈 <b>Cache Savings</b>: [{bar}] <b>{cache_pct:.1f}%</b>\n"
    text += f"🛡️ <b>Token Saver</b>: Caveman {'🟢' if caveman_on else '🔴'} • Ponytail {'🟢' if ponytail_on else '🔴'}\n\n"
    
    text += "👥 <b>Active Connections Pool:</b>\n"
    for idx, acc in enumerate(accounts, 1):
        status_dot = "🟢" if acc["active"] else "🔴"
        last_used = acc["lastUsedAt"][11:19] if acc.get("lastUsedAt") else "Never"
        text += f"{idx}. {status_dot} <b>[{acc['provider'].upper()}]</b> <code>{acc['email']}</code>\n"
        
    return text

def format_token_saver_dashboard(settings):
    caveman_on = settings.get("cavemanEnabled", False)
    caveman_lvl = settings.get("cavemanLevel", "full")
    ponytail_on = settings.get("ponytailEnabled", False)
    
    text = "🛡️ <b>9ROUTER TOKEN SAVER & COMPRESSION HUB</b> 🛡️\n\n"
    text += "Konfigurasi kompresi prompt & output untuk menghemat token dan cost kuota:\n\n"
    
    text += "1. <b>Compress LLM Output (Caveman)</b>:\n"
    text += f"   • Status: <b>{'🟢 AKTIF' if caveman_on else '🔴 NONAKTIF'}</b>\n"
    text += f"   • Mode  : <code>{caveman_lvl.upper()}</code>\n"
    text += "   └ <i>Menghapus filler/basa-basi AI, respon lebih padat & hemat token.</i>\n\n"
    
    text += "2. <b>Lazy Senior Dev Code Filter (Ponytail)</b>:\n"
    text += f"   • Status: <b>{'🟢 AKTIF' if ponytail_on else '🔴 NONAKTIF'}</b>\n"
    text += "   └ <i>Menulis kode minimalis, menghapus boilerplate/scaffolding berlebih.</i>\n\n"
    
    text += "<i>Klik tombol di bawah untuk toggle ON/OFF fitur secara realtime:</i>"
    return text

def format_account_detailed_quota(data, target_email=None):
    api = data.get("api", {})
    by_account = api.get("byAccount", {})
    accounts = data.get("accounts", [])
    
    text = "🔍 <b>ACCOUNT DETAILED QUOTA & CONSUMPTION</b>\n\n"
    
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
        status_str = "🟢 ACTIVE (In Pool)" if (conn_info and conn_info["active"]) else "🔴 DISABLED"
        
        text += f"👤 <b>Account:</b> <code>{target_email}</code>\n"
        text += f"• Status: {status_str}\n\n"
        
        if acc_info:
            p_m = acc_info["promptTokens"] / 1_000_000
            c_m = acc_info["cachedTokens"] / 1_000_000
            comp_k = acc_info["completionTokens"] / 1_000
            c_pct = (c_m / p_m * 100) if p_m > 0 else 0
            
            text += f"📊 <b>Token Statistics:</b>\n"
            text += f" • Requests Count  : <b>{acc_info['requests']:,}x</b>\n"
            text += f" • Prompt Ingested : <b>{p_m:.2f} M</b>\n"
            text += f" • Cached Tokens   : <b>{c_m:.2f} M ({c_pct:.1f}%)</b> ⚡\n"
            text += f" • Output Generated: <b>{comp_k:.2f} K</b>\n"
            text += f" • Cumulative Cost : <b>${acc_info['cost']:.4f}</b>\n\n"
            
            text += f"🧠 <b>Model Ingestion Breakdown:</b>\n"
            for m in acc_info["models"]:
                text += f" └ <code>{m['model']}</code> : <b>{m['reqs']}x</b> (${m['cost']:.4f})\n"
        else:
            text += "<i>No request history logged for this account today.</i>\n"
        return text

    for idx, (email, st) in enumerate(acc_map.items(), 1):
        p_m = st["promptTokens"] / 1_000_000
        text += f"{idx}. 🟢 <code>{email}</code>\n"
        text += f"   • Requests : <b>{st['requests']}x</b> | Tokens: <b>{p_m:.2f}M</b> | Cost: <b>${st['cost']:.4f}</b>\n\n"
        
    return text

def format_recent_logs(data):
    recent = data.get("recent", [])
    text = "📋 <b>TRANSACTION AUDIT LOGS (REALTIME)</b>\n\n"
    if not recent:
        return text + "<i>No requests recorded yet.</i>"
        
    for r in recent:
        status_icon = "✅" if r["status"] == "ok" else "⚠️"
        p_k = r["prompt"] / 1000
        text += f"{status_icon} <b>[{r['time']}]</b> <code>{r['model']}</code>\n"
        text += f"   └ Volume: <b>{p_k:.1f}k in / {r['comp']} out</b> • Cost: <b>${r['cost']:.5f}</b>\n"
    return text

def format_models_breakdown(data):
    daily = data.get("daily", {})
    by_model = daily.get("byModel", {})
    
    text = "🧠 <b>ACTIVE MODEL USAGE BREAKDOWN</b>\n\n"
    if not by_model:
        return text + "<i>No model statistics available today.</i>"
        
    for model_key, stats in by_model.items():
        m_name = stats.get("rawModel") or model_key
        reqs = stats.get("requests", 0)
        p_m = stats.get("promptTokens", 0) / 1_000_000
        cost = stats.get("cost", 0.0)
        text += f"🔹 <b>{m_name}</b>\n"
        text += f"   • Volume : <b>{reqs}x requests</b> | <b>{p_m:.2f} M tokens</b>\n"
        text += f"   • Cost   : <b>${cost:.4f}</b>\n\n"
    return text
