import time

def format_quota_report(data):
    api = data.get("api", {})
    daily = data.get("daily", {})
    accounts = data.get("accounts", [])
    settings = data.get("settings", {})
    antigravity = data.get("antigravity", {})
    period = data.get("period", "today").upper()
    
    total_req = api.get("totalRequests") or daily.get("requests") or 0
    prompt_tokens = (api.get("totalPromptTokens") or daily.get("promptTokens") or 0) / 1_000_000
    comp_tokens = (api.get("totalCompletionTokens") or daily.get("completionTokens") or 0) / 1_000
    cached_tokens = (api.get("totalCachedTokens") or 0) / 1_000_000
    cost = api.get("totalCost") or daily.get("cost") or 0.0
    
    agy_sessions = antigravity.get("sessions", 0)
    agy_steps = antigravity.get("steps", 0)
    agy_cost = antigravity.get("est_cost", 0.0)

    hermes_info = data.get("hermes_lifetime", {})
    hermes_cost = hermes_info.get("cost", cost)
    hermes_reqs = hermes_info.get("requests", total_req)
    total_combined = hermes_cost + agy_cost

    rr_limit = settings.get("stickyRoundRobinLimit", 3)
    caveman_on = settings.get("cavemanEnabled", False)
    ponytail_on = settings.get("ponytailEnabled", False)
    
    cache_pct = (cached_tokens / prompt_tokens * 100) if prompt_tokens > 0 else 0
    
    text = f"⚡ <b>9ROUTER INFRASTRUCTURE HUB ({period})</b> ⚡\n"
    text += f"<code>Balancer: Round-Robin ({rr_limit}x) • {time.strftime('%H:%M:%S')} UTC</code>\n\n"
    
    text += "┌─────────────────────────────────────┐\n"
    text += f"│ 🚀 <b>TELEMETRY ({period})</b>\n"
    text += f"│ • Requests: <b>{total_req:,}x</b> | Cost: <b>${cost:.4f}</b>\n"
    text += f"│ • Ingest: <b>{prompt_tokens:.2f}M</b> | Cached: <b>{cached_tokens:.2f}M ({cache_pct:.1f}%)</b>\n"
    text += f"│ • Output: <b>{comp_tokens:.2f}K tokens</b>\n"
    text += "├─────────────────────────────────────┤\n"
    text += "│ 🤖 <b>ANTIGRAVITY CLI</b>\n"
    text += f"│ • Sessions: <b>{agy_sessions:,}</b> | Steps: <b>{agy_steps:,}</b>\n"
    text += "├─────────────────────────────────────┤\n"
    text += "│ 💰 <b>BIAYA TOTAL & KOMPARASI</b>\n"
    text += f"│ • Hermes Chat : <b>${hermes_cost:.2f}</b> ({hermes_reqs:,} reqs)\n"
    text += f"│ • agy Engine  : <b>${agy_cost:.2f}</b> ({agy_steps:,} steps)\n"
    text += f"│ • Total Biaya : <b>${total_combined:.2f}</b>\n"
    text += "└─────────────────────────────────────┘\n\n"

    text += f"🛡️ <b>Saver</b>: Caveman {'🟢' if caveman_on else '🔴'} • Ponytail {'🟢' if ponytail_on else '🔴'}\n"
    text += "👥 <b>Active Pool:</b> "
    
    acc_items = []
    for acc in accounts:
        status_dot = "🟢" if acc["active"] else "🔴"
        acc_items.append(f"{status_dot} <code>{acc['email']}</code>")
    
    if acc_items:
        text += ", ".join(acc_items)
    else:
        text += "<i>None</i>"

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
    daily = data.get("daily", {})
    accounts = data.get("accounts", [])
    
    text = "🔍 <b>ACCOUNT DETAILED QUOTA & CONSUMPTION</b>\n\n"
    
    conn_by_id = {}
    conn_by_email = {}
    for acc in accounts:
        cid = acc.get("id")
        email = acc.get("email")
        name = acc.get("name")
        if cid:
            conn_by_id[cid] = acc
        if email:
            conn_by_email[email] = acc
            conn_by_email[email.lower()] = acc
        if name:
            conn_by_email[name] = acc
            conn_by_email[name.lower()] = acc

    by_account = api.get("byAccount") or daily.get("byAccount") or {}
    
    acc_map = {}
    for k, v in by_account.items():
        conn_id = v.get("connectionId") or (k if k in conn_by_id else None)
        conn_info = None
        if conn_id and conn_id in conn_by_id:
            conn_info = conn_by_id[conn_id]
        else:
            acct_name = v.get("accountName")
            if acct_name and acct_name in conn_by_email:
                conn_info = conn_by_email[acct_name]
            elif k in conn_by_email:
                conn_info = conn_by_email[k]
            else:
                for em, acc_obj in conn_by_email.items():
                    if em in k:
                        conn_info = acc_obj
                        break

        if conn_info:
            acc_email = conn_info["email"]
            acc_name = conn_info["name"]
            acc_active = conn_info["active"]
            acc_provider = conn_info["provider"]
        else:
            acc_email = v.get("accountName") or k
            acc_name = acc_email
            acc_active = False
            acc_provider = v.get("provider", "unknown")

        if acc_email not in acc_map:
            acc_map[acc_email] = {
                "email": acc_email,
                "name": acc_name,
                "provider": acc_provider,
                "active": acc_active,
                "requests": 0,
                "promptTokens": 0,
                "cachedTokens": 0,
                "completionTokens": 0,
                "cost": 0.0,
                "models": {}
            }

        entry = acc_map[acc_email]
        entry["requests"] += v.get("requests", 0)
        entry["promptTokens"] += v.get("promptTokens", 0)
        entry["cachedTokens"] += v.get("cachedTokens", 0)
        entry["completionTokens"] += v.get("completionTokens", 0)
        entry["cost"] += v.get("cost", 0.0)

        raw_model = v.get("rawModel") or v.get("model") or "unknown"
        if raw_model not in entry["models"]:
            entry["models"][raw_model] = {"reqs": 0, "cost": 0.0}
        entry["models"][raw_model]["reqs"] += v.get("requests", 0)
        entry["models"][raw_model]["cost"] += v.get("cost", 0.0)

    if target_email:
        acc_info = acc_map.get(target_email)
        if not acc_info:
            target_lower = target_email.lower()
            for em, info in acc_map.items():
                if em.lower() == target_lower:
                    acc_info = info
                    break
        
        conn_info = conn_by_email.get(target_email) or conn_by_email.get(target_email.lower()) or next((a for a in accounts if a["email"] == target_email or a["id"] == target_email), None)
        
        acc_name_display = acc_info["name"] if acc_info else (conn_info["name"] if conn_info else target_email)
        acc_email_display = acc_info["email"] if acc_info else (conn_info["email"] if conn_info else target_email)
        is_active = acc_info["active"] if acc_info else (conn_info["active"] if conn_info else False)
        provider_name = acc_info["provider"] if acc_info else (conn_info["provider"] if conn_info else "UNKNOWN")

        status_str = "🟢 ACTIVE (In Pool)" if is_active else "🔴 DISABLED"

        text += f"👤 <b>Account:</b> <code>{acc_email_display}</code>\n"
        if acc_name_display and acc_name_display != acc_email_display:
            text += f"• <b>Name:</b> <code>{acc_name_display}</code>\n"
        text += f"• <b>Provider:</b> <code>{provider_name.upper()}</code>\n"
        text += f"• <b>Status:</b> {status_str}\n\n"

        if acc_info and acc_info["requests"] > 0:
            p_m = acc_info["promptTokens"] / 1_000_000
            c_m = acc_info["cachedTokens"] / 1_000_000
            comp_k = acc_info["completionTokens"] / 1_000
            c_pct = (c_m / p_m * 100) if p_m > 0 else 0

            text += "📊 <b>Token Statistics:</b>\n"
            text += f" • Requests Count  : <b>{acc_info['requests']:,}x</b>\n"
            text += f" • Prompt Ingested : <b>{p_m:.2f} M</b>\n"
            text += f" • Cached Tokens   : <b>{c_m:.2f} M ({c_pct:.1f}%)</b> ⚡\n"
            text += f" • Output Generated: <b>{comp_k:.2f} K</b>\n"
            text += f" • Cumulative Cost : <b>${acc_info['cost']:.4f}</b>\n\n"

            text += "🧠 <b>Model Ingestion Breakdown:</b>\n"
            for m_name, m_data in acc_info["models"].items():
                text += f" └ <code>{m_name}</code> : <b>{m_data['reqs']}x</b> (${m_data['cost']:.4f})\n"
        else:
            text += "<i>No request history logged for this account today.</i>\n"
        return text

    if not accounts and not acc_map:
        return text + "<i>No accounts configured or usage logged today.</i>"

    seen_emails = set()
    idx = 1
    for acc in accounts:
        email = acc["email"]
        seen_emails.add(email)
        status_dot = "🟢" if acc["active"] else "🔴"
        st = acc_map.get(email)
        if st:
            p_m = st["promptTokens"] / 1_000_000
            comp_k = st["completionTokens"] / 1_000
            text += f"{idx}. {status_dot} <b>[{acc['provider'].upper()}]</b> <code>{email}</code>\n"
            text += f"   • Requests : <b>{st['requests']}x</b> | Ingest: <b>{p_m:.2f}M</b> | Out: <b>{comp_k:.2f}K</b> | Cost: <b>${st['cost']:.4f}</b>\n\n"
        else:
            text += f"{idx}. {status_dot} <b>[{acc['provider'].upper()}]</b> <code>{email}</code>\n"
            text += "   • Requests : <b>0x</b> | Ingest: <b>0.00M</b> | Out: <b>0.00K</b> | Cost: <b>$0.0000</b>\n\n"
        idx += 1

    for email, st in acc_map.items():
        if email not in seen_emails:
            status_dot = "🟢" if st["active"] else "🔴"
            p_m = st["promptTokens"] / 1_000_000
            comp_k = st["completionTokens"] / 1_000
            text += f"{idx}. {status_dot} <b>[{st['provider'].upper()}]</b> <code>{email}</code>\n"
            text += f"   • Requests : <b>{st['requests']}x</b> | Ingest: <b>{p_m:.2f}M</b> | Out: <b>{comp_k:.2f}K</b> | Cost: <b>${st['cost']:.4f}</b>\n\n"
            idx += 1

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

def format_combos_adapters_dashboard(data):
    combos = data.get("combos", [])
    adapters = data.get("adapters", {})
    
    vision = adapters.get("vision", {})
    audio = adapters.get("audioInput", {})

    text = "🔀 <b>COMBOS & MODALITY ADAPTERS HUB</b> 🔀\n\n"
    
    # 1. Combos section
    text += "📦 <b>MODEL COMBOS (FALLBACK & FUSION)</b>:\n"
    if combos:
        for c in combos:
            kind_str = c.get("kind", "fallback").upper()
            m_list = ", ".join([f"<code>{m}</code>" for m in c.get("models", [])])
            text += f" • <b>{c.get('name')}</b> (<code>{kind_str}</code>)\n"
            text += f"   └ Models: {m_list if m_list else '<i>None</i>'}\n"
    else:
        text += " <i>Belum ada combo terkonfigurasi.</i>\n"
        
    text += "\n┌─────────────────────────────────────┐\n"
    text += "│ 👁️ <b>VISION CAPACITY ADAPTER</b>\n"
    text += f"│ • Status      : <b>{'🟢 ENABLED' if vision.get('enabled') else '🔴 DISABLED'}</b>\n"
    text += f"│ • Round-Robin : <b>{'🟢 ON' if vision.get('roundRobin') else '🔴 OFF'}</b>\n"
    v_models = ", ".join([f"<code>{m}</code>" for m in vision.get("models", [])])
    text += f"│ • Models      : {v_models if v_models else '<i>None</i>'}\n"
    text += "├─────────────────────────────────────┤\n"
    text += "│ 🎙️ <b>AUDIO INPUT ADAPTER</b>\n"
    text += f"│ • Status      : <b>{'🟢 ENABLED' if audio.get('enabled') else '🔴 DISABLED'}</b>\n"
    text += f"│ • Round-Robin : <b>{'🟢 ON' if audio.get('roundRobin') else '🔴 OFF'}</b>\n"
    a_models = ", ".join([f"<code>{m}</code>" for m in audio.get("models", [])])
    text += f"│ • Models      : {a_models if a_models else '<i>None</i>'}\n"
    text += "└─────────────────────────────────────┘\n\n"
    
    text += "<i>Gunakan tombol di bawah untuk mengelola adapter & combo:</i>"
    return text

