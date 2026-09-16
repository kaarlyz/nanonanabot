import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes, ConversationHandler

from services.router_service import (
    fetch_9router_stats,
    toggle_account_db,
    delete_account_db,
    set_round_robin_limit,
    add_custom_provider_db,
    exchange_oauth_antigravity,
    fetch_available_models_catalog,
    get_opencode_config_details,
    set_opencode_main_model_file,
    add_opencode_model_file,
    delete_opencode_model_file,
    get_auth_token,
)
from utils.formatter import (
    format_quota_report,
    format_recent_logs,
    format_models_breakdown,
    format_account_detailed_quota,
)
from core.keyboards import get_main_menu_keyboard, get_back_button
from config.settings import BASE_URL, BANNER_IMAGE_PATH

ADD_NAME, ADD_KEY, ADD_URL, ADD_OAUTH_CALLBACK = range(4)

async def safe_edit_message(query, text, reply_markup):
    try:
        if query.message.caption:
            await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            pass
        else:
            try:
                await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=reply_markup)
            except:
                pass

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = fetch_9router_stats()
    text = format_quota_report(data)
    reply_markup = get_main_menu_keyboard()
    
    if update.message:
        if os.path.exists(BANNER_IMAGE_PATH):
            with open(BANNER_IMAGE_PATH, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_html(text, reply_markup=reply_markup)
    elif update.callback_query:
        await safe_edit_message(update.callback_query, text, reply_markup)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = fetch_9router_stats()
    
    if query.data in ["refresh_quota", "view_quota"]:
        text = format_quota_report(data)
        await safe_edit_message(query, text, get_main_menu_keyboard())
        
    elif query.data == "view_logs":
        text = format_recent_logs(data)
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh Logs", callback_data="view_logs"),
                InlineKeyboardButton("⬅️ Return to Dashboard", callback_data="view_quota")
            ]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "view_models":
        text = format_models_breakdown(data)
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="view_models"),
                InlineKeyboardButton("⬅️ Return to Dashboard", callback_data="view_quota")
            ]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "detailed_quota_menu":
        accounts = data.get("accounts", [])
        text = "📊 <b>ACCOUNT CONSUMPTION & QUOTA AUDIT</b>\n\n"
        text += "Select an account to view dedicated token stats and lifetime metrics:\n\n"
        
        keyboard = []
        for acc in accounts:
            label = f"👤 {acc['email']}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"show_acc_quota_{acc['email']}")])
            
        keyboard.append([InlineKeyboardButton("⬅️ Return to Dashboard", callback_data="view_quota")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("show_acc_quota_"):
        email = query.data.replace("show_acc_quota_", "")
        text = format_account_detailed_quota(data, target_email=email)
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh Stats", callback_data=f"show_acc_quota_{email}")],
            [InlineKeyboardButton("⬅️ Select Another Account", callback_data="detailed_quota_menu")],
            [InlineKeyboardButton("🏠 Main Dashboard", callback_data="view_quota")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "manage_accounts":
        accounts = data.get("accounts", [])
        text = "⚙️ <b>PROVIDER & ACCOUNT MANAGEMENT</b>\n\n"
        text += "Select a connection below to toggle state or permanently remove from pool:\n\n"
        
        keyboard = []
        for acc in accounts:
            status_emoji = "🟢" if acc["active"] else "🔴"
            label = f"{status_emoji} [{acc['provider'].upper()}] {acc['email'][:20]}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"acc_detail_{acc['id']}")])
            
        keyboard.append([InlineKeyboardButton("⬅️ Return to Dashboard", callback_data="view_quota")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("acc_detail_"):
        acc_id = query.data.replace("acc_detail_", "")
        accounts = data.get("accounts", [])
        acc = next((a for a in accounts if a["id"] == acc_id), None)
        if not acc:
            await query.answer("Account not found")
            return
            
        status_text = "🟢 ACTIVE" if acc["active"] else "🔴 DISABLED"
        toggle_label = "🔴 Disable Account" if acc["active"] else "🟢 Enable Account"
        
        text = f"👤 <b>CONNECTION PROFILE:</b>\n\n"
        text += f"• <b>Identifier</b>: <code>{acc['email']}</code>\n"
        text += f"• <b>Provider</b>: <code>{acc['provider'].upper()}</code>\n"
        text += f"• <b>Status</b>: {status_text}\n"
        text += f"• <b>Connection ID</b>: <code>{acc['id']}</code>\n\n"
        text += "<i>Select an action:</i>"
        
        keyboard = [
            [InlineKeyboardButton(toggle_label, callback_data=f"toggle_{acc['id']}")],
            [InlineKeyboardButton("📊 View Token Stats", callback_data=f"show_acc_quota_{acc['email']}")],
            [InlineKeyboardButton("🗑️ Delete Account", callback_data=f"del_confirm_{acc['id']}")],
            [InlineKeyboardButton("⬅️ Back to Accounts", callback_data="manage_accounts")]
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
            status_text = "🟢 ACTIVE" if acc["active"] else "🔴 DISABLED"
            toggle_label = "🔴 Disable Account" if acc["active"] else "🟢 Enable Account"
            text = f"👤 <b>CONNECTION PROFILE:</b>\n\n{msg}\n\n"
            text += f"• <b>Identifier</b>: <code>{acc['email']}</code>\n"
            text += f"• <b>Provider</b>: <code>{acc['provider'].upper()}</code>\n"
            text += f"• <b>Status</b>: {status_text}\n\n"
            keyboard = [
                [InlineKeyboardButton(toggle_label, callback_data=f"toggle_{acc['id']}")],
                [InlineKeyboardButton("📊 View Token Stats", callback_data=f"show_acc_quota_{acc['email']}")],
                [InlineKeyboardButton("🗑️ Delete Account", callback_data=f"del_confirm_{acc['id']}")],
                [InlineKeyboardButton("⬅️ Back to Accounts", callback_data="manage_accounts")]
            ]
            await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
            
    elif query.data.startswith("del_confirm_"):
        acc_id = query.data.replace("del_confirm_", "")
        accounts = data.get("accounts", [])
        acc = next((a for a in accounts if a["id"] == acc_id), None)
        name = acc["email"] if acc else acc_id
        
        text = f"⚠️ <b>CONFIRM ACCOUNT REMOVAL</b>\n\n"
        text += f"Are you sure you want to delete <code>{name}</code> from 9Router?\n"
        text += "<i>This action is permanent and cannot be undone.</i>"
        
        keyboard = [
            [InlineKeyboardButton("🔥 Confirm Delete", callback_data=f"del_do_{acc_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"acc_detail_{acc_id}")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("del_do_"):
        acc_id = query.data.replace("del_do_", "")
        ok, msg = delete_account_db(acc_id)
        await query.answer(msg)
        
        text = f"{msg}\n\nUse /quota to return to dashboard."
        keyboard = [[InlineKeyboardButton("⬅️ Back to Accounts", callback_data="manage_accounts")]]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "rr_menu":
        settings = data.get("settings", {})
        cur_limit = settings.get("stickyRoundRobinLimit", 3)
        
        text = "🎯 <b>ROUND-ROBIN ROTATION CONFIGURATION</b>\n\n"
        text += f"• <b>Current Sticky Limit</b>: <b>{cur_limit} consecutive requests per account</b>\n"
        text += "• <b>Strategy</b>: Balanced dynamic rotation across all active pool members.\n\n"
        text += "<i>Select request limit before rotating to next pool connection:</i>"
        
        keyboard = [
            [
                InlineKeyboardButton("1x (Strict Dynamic)", callback_data="set_rr_1"),
                InlineKeyboardButton("2x", callback_data="set_rr_2"),
                InlineKeyboardButton("3x (Recommended)", callback_data="set_rr_3")
            ],
            [
                InlineKeyboardButton("5x", callback_data="set_rr_5"),
                InlineKeyboardButton("10x", callback_data="set_rr_10")
            ],
            [InlineKeyboardButton("⬅️ Return to Dashboard", callback_data="view_quota")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("set_rr_"):
        val = int(query.data.replace("set_rr_", ""))
        ok, msg = set_round_robin_limit(val)
        await query.answer(msg)
        
        text = f"🎯 <b>ROUND-ROBIN ROTATION CONFIGURATION</b>\n\n{msg}\n\n<i>Adjust settings or return:</i>"
        keyboard = [
            [
                InlineKeyboardButton("1x", callback_data="set_rr_1"),
                InlineKeyboardButton("2x", callback_data="set_rr_2"),
                InlineKeyboardButton("3x", callback_data="set_rr_3"),
                InlineKeyboardButton("5x", callback_data="set_rr_5"),
                InlineKeyboardButton("10x", callback_data="set_rr_10")
            ],
            [InlineKeyboardButton("⬅️ Return to Dashboard", callback_data="view_quota")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "cli_tools_menu":
        opencode_info = get_opencode_config_details()
        models = opencode_info["models"]
        main_m = opencode_info["main_model"]
        
        text = "💻 <b>OPENCODE CLI ENGINE INTEGRATION</b>\n\n"
        text += f"⭐ <b>Active Primary Model:</b>\n👉 <code>{main_m}</code>\n\n"
        text += f"📦 <b>Configured Models Pool ({len(models)}):</b>\n"
        for m in models:
            is_active_main = (m == main_m or f"9router/{m}" == main_m)
            prefix = "⭐ [PRIMARY] " if is_active_main else "• "
            text += f"{prefix}<code>{m}</code>\n"
            
        text += "\n<i>Choose an operation:</i>"
        keyboard = [
            [InlineKeyboardButton("⭐ Set Default / Main Model", callback_data="opencode_set_main_menu")],
            [InlineKeyboardButton("📥 Add from 9Router Catalog", callback_data="pick_catalog_models_0")],
            [InlineKeyboardButton("🗑️ Remove Configured Model", callback_data="opencode_del_list")],
            [InlineKeyboardButton("⬅️ Return to Dashboard", callback_data="view_quota")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "opencode_set_main_menu":
        opencode_info = get_opencode_config_details()
        models = opencode_info["models"]
        main_m = opencode_info["main_model"]
        
        text = "⭐ <b>SELECT PRIMARY MODEL FOR OPENCODE CLI</b>\n\n"
        text += f"Current Primary: <code>{main_m}</code>\n\n"
        text += "<i>Click a model below to assign it as default runtime engine:</i>\n\n"
        
        keyboard = []
        for m in models:
            is_active_main = (m == main_m or f"9router/{m}" == main_m)
            tag = "✅ " if is_active_main else "🔹 "
            keyboard.append([InlineKeyboardButton(f"{tag}{m}", callback_data=f"set_opencode_main_{m[:30]}")])
            
        keyboard.append([InlineKeyboardButton("⬅️ Back to CLI Tools", callback_data="cli_tools_menu")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("set_opencode_main_"):
        target_short = query.data.replace("set_opencode_main_", "")
        opencode_info = get_opencode_config_details()
        full_model = next((m for m in opencode_info["models"] if m.startswith(target_short)), target_short)
        
        ok, msg = set_opencode_main_model_file(full_model)
        await query.answer("Primary model updated successfully!")
        
        text = f"⭐ <b>PRIMARY MODEL UPDATED</b>\n\n{msg}\n\nOpencode CLI will now use this model by default."
        keyboard = [
            [InlineKeyboardButton("💻 Return to Opencode Manager", callback_data="cli_tools_menu")],
            [InlineKeyboardButton("🏠 Main Dashboard", callback_data="view_quota")]
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
        
        text = f"📥 <b>9ROUTER CATALOG BROWSER (Page {page+1}/{total_pages})</b>\n\n"
        text += "Click any model below to <b>INSTANTLY REGISTER</b> into Opencode CLI:\n\n"
        
        keyboard = []
        for m in cur_items:
            is_added = m in active_opencode
            status_tag = "✅ (Active)" if is_added else "➕ Add"
            keyboard.append([InlineKeyboardButton(f"{status_tag} {m}", callback_data=f"btn_add_model_{m}")])
            
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"pick_catalog_models_{page-1}"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"pick_catalog_models_{page+1}"))
            
        if nav_row:
            keyboard.append(nav_row)
        keyboard.append([InlineKeyboardButton("⬅️ Back to CLI Tools", callback_data="cli_tools_menu")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("btn_add_model_"):
        model_to_add = query.data.replace("btn_add_model_", "")
        ok, msg = add_opencode_model_file(model_to_add)
        await query.answer(f"{model_to_add} added!")
        
        catalog = fetch_available_models_catalog("antigravity")
        active_opencode = set(get_opencode_config_details()["models"])
        page = 0
        per_page = 6
        total_pages = (len(catalog) + per_page - 1) // per_page
        cur_items = catalog[:per_page]
        
        text = f"📥 <b>9ROUTER CATALOG BROWSER</b>\n\n{msg}\n\n"
        keyboard = []
        for m in cur_items:
            is_added = m in active_opencode
            status_tag = "✅ (Active)" if is_added else "➕ Add"
            keyboard.append([InlineKeyboardButton(f"{status_tag} {m}", callback_data=f"btn_add_model_{m}")])
            
        if total_pages > 1:
            keyboard.append([InlineKeyboardButton("Next ➡️", callback_data="pick_catalog_models_1")])
        keyboard.append([InlineKeyboardButton("⬅️ Back to CLI Tools", callback_data="cli_tools_menu")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "opencode_del_list":
        models = get_opencode_config_details()["models"]
        text = "🗑️ <b>REMOVE CONFIGURED MODEL</b>\n\nClick a model below to delete from Opencode configuration:\n\n"
        keyboard = []
        for m in models:
            keyboard.append([InlineKeyboardButton(f"❌ {m}", callback_data=f"del_opencode_{m[:30]}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="cli_tools_menu")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data.startswith("del_opencode_"):
        m_name = query.data.replace("del_opencode_", "")
        models = get_opencode_config_details()["models"]
        full_m = next((m for m in models if m.startswith(m_name)), m_name)
        ok, msg = delete_opencode_model_file(full_m)
        await query.answer(msg)
        
        models = get_opencode_config_details()["models"]
        text = f"🗑️ <b>REMOVE CONFIGURED MODEL</b>\n\n{msg}\n\n"
        keyboard = []
        for m in models:
            keyboard.append([InlineKeyboardButton(f"❌ {m}", callback_data=f"del_opencode_{m[:30]}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back to CLI Tools", callback_data="cli_tools_menu")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        
    elif query.data == "add_provider_menu":
        text = "➕ <b>SELECT PROVIDER INFRASTRUCTURE TYPE</b>\n\n"
        text += "Choose authentication type to link into 9Router gateway:\n\n"
        text += "1. <b>Google Antigravity (Gemini / Claude Pro-Tier Pool)</b>\n"
        text += "2. <b>Groq / DeepSeek / OpenAI / OpenRouter</b> (API Key)\n"
        text += "3. <b>Custom OpenAI Compatible</b> (Key + Private Base URL)\n"
        
        keyboard = [
            [InlineKeyboardButton("🚀 Google Antigravity (OAuth)", callback_data="prov_type_antigravity")],
            [InlineKeyboardButton("🟣 Groq API", callback_data="prov_type_groq"), InlineKeyboardButton("🔵 DeepSeek API", callback_data="prov_type_deepseek")],
            [InlineKeyboardButton("🟢 OpenAI API", callback_data="prov_type_openai"), InlineKeyboardButton("🟠 OpenRouter", callback_data="prov_type_openrouter")],
            [InlineKeyboardButton("🌐 Custom OpenAI-Compatible", callback_data="prov_type_custom")],
            [InlineKeyboardButton("⬅️ Return to Dashboard", callback_data="view_quota")]
        ]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))

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
            
            text = "🚀 <b>GOOGLE ANTIGRAVITY OAUTH RELAY</b>\n\n"
            text += "1. Open Google OAuth authorization link:\n"
            text += f"👉 <a href=\"{auth_url}\"><b>AUTHENTICATE WITH GOOGLE</b></a>\n\n"
            text += "2. Select target Google account and click <b>Allow</b>.\n\n"
            text += "3. Copy the resulting URL from your address bar (<code>http://localhost:8080/callback?code=...</code>).\n\n"
            text += "4. <b>Paste the callback link into this chat</b>:\n\n"
            text += "<i>Send /cancel to abort.</i>"
            
            await safe_edit_message(query, text, None)
            return ADD_OAUTH_CALLBACK
        except Exception as e:
            await query.edit_message_text(f"❌ OAuth generation failed: {e}")
            return ConversationHandler.END
            
    text = f"📝 <b>Add Provider [{prov_type.upper()}]</b>\n\n"
    text += "Enter a <b>Label/Display Name</b> for this provider (e.g. <code>Production Key</code>):\n\n"
    text += "<i>Send /cancel to abort.</i>"
    
    await safe_edit_message(query, text, None)
    return ADD_NAME

async def wizard_oauth_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    session_auth_data = context.user_data.get("oauth_data", {})
    
    await update.message.reply_text("⏳ Exchanging OAuth tokens with Google Cloud and 9Router...")
    ok, msg = exchange_oauth_antigravity(user_input, session_auth_data)
    
    keyboard = [[InlineKeyboardButton("📊 Return to Dashboard", callback_data="view_quota")]]
    await update.message.reply_html(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def wizard_name_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["prov_name"] = name
    prov_type = context.user_data.get("prov_type")
    
    text = f"🔑 Enter <b>API Key</b> for <b>{name}</b> ({prov_type.upper()}):\n\n"
    text += "<i>Secret values are safely encrypted into 9Router SQLite.</i>"
    
    await update.message.reply_html(text)
    return ADD_KEY

async def wizard_key_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = update.message.text.strip()
    context.user_data["prov_key"] = api_key
    prov_type = context.user_data.get("prov_type")
    name = context.user_data.get("prov_name")
    
    if prov_type == "custom":
        text = f"🌐 Enter <b>Base URL Endpoint</b> (e.g. <code>https://api.together.xyz/v1</code>):\n"
        await update.message.reply_html(text)
        return ADD_URL
    else:
        ok, msg = add_custom_provider_db(prov_type, name, api_key)
        keyboard = [[InlineKeyboardButton("📊 Return to Dashboard", callback_data="view_quota")]]
        await update.message.reply_html(f"{msg}\n\nModels from this provider are now live in 9Router!", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

async def wizard_url_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    custom_url = update.message.text.strip()
    api_key = context.user_data.get("prov_key")
    name = context.user_data.get("prov_name")
    prov_type = context.user_data.get("prov_type")
    
    ok, msg = add_custom_provider_db(prov_type, name, api_key, custom_url)
    keyboard = [[InlineKeyboardButton("📊 Return to Dashboard", callback_data="view_quota")]]
    await update.message.reply_html(f"{msg}\n\nCustom endpoint successfully linked to 9Router!", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def cancel_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Wizard cancelled. Send /quota to return to dashboard.")
    return ConversationHandler.END
