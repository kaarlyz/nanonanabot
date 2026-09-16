from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard(period="today"):
    # Timeframe selection indicator
    p_today = "🔘 Today" if period == "today" else "Today"
    p_24h = "🔘 24h" if period == "24h" else "24h"
    p_7d = "🔘 7d" if period == "7d" else "7d"
    p_30d = "🔘 30d" if period == "30d" else "30d"
    p_all = "🔘 1y/All" if period == "all" else "1y/All"
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(p_today, callback_data="period_today"),
            InlineKeyboardButton(p_24h, callback_data="period_24h"),
            InlineKeyboardButton(p_7d, callback_data="period_7d"),
            InlineKeyboardButton(p_30d, callback_data="period_30d"),
            InlineKeyboardButton(p_all, callback_data="period_all"),
        ],
        [
            InlineKeyboardButton("🔄 Refresh Dashboard", callback_data=f"refresh_{period}"),
            InlineKeyboardButton("🛡️ Token Saver Hub", callback_data="token_saver_menu")
        ],
        [
            InlineKeyboardButton("📊 Per-Account Quota", callback_data="detailed_quota_menu"),
            InlineKeyboardButton("📋 Transaction Logs", callback_data="view_logs")
        ],
        [
            InlineKeyboardButton("🧠 Model Breakdown", callback_data="view_models"),
            InlineKeyboardButton("🎯 Round-Robin Limit", callback_data="rr_menu")
        ],
        [
            InlineKeyboardButton("⚙️ Kelola Akun & Hapus", callback_data="manage_accounts"),
            InlineKeyboardButton("💻 Opencode CLI Manager", callback_data="cli_tools_menu")
        ],
        [
            InlineKeyboardButton("➕ Tambah Provider Baru", callback_data="add_provider_menu")
        ]
    ])

def get_token_saver_keyboard(settings):
    caveman_on = settings.get("cavemanEnabled", False)
    caveman_lvl = settings.get("cavemanLevel", "full")
    ponytail_on = settings.get("ponytailEnabled", False)
    
    btn_caveman = "🟢 Caveman: ON" if caveman_on else "🔴 Caveman: OFF"
    btn_level = f"⚡ Level: {caveman_lvl.upper()}"
    btn_ponytail = "🟢 Ponytail: ON" if ponytail_on else "🔴 Ponytail: OFF"
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(btn_caveman, callback_data="ts_toggle_caveman"),
            InlineKeyboardButton(btn_level, callback_data="ts_toggle_level")
        ],
        [
            InlineKeyboardButton(btn_ponytail, callback_data="ts_toggle_ponytail")
        ],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="token_saver_menu"),
            InlineKeyboardButton("⬅️ Return to Dashboard", callback_data="view_quota")
        ]
    ])

def get_back_button(callback_data="view_quota"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Return to Dashboard", callback_data=callback_data)]])
