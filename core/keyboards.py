from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh Dashboard", callback_data="refresh_quota"),
            InlineKeyboardButton("📋 Audit Logs", callback_data="view_logs")
        ],
        [
            InlineKeyboardButton("📊 Per-Account Quota", callback_data="detailed_quota_menu"),
            InlineKeyboardButton("🧠 Model Breakdown", callback_data="view_models")
        ],
        [
            InlineKeyboardButton("⚙️ Account Management", callback_data="manage_accounts"),
            InlineKeyboardButton("🎯 Round-Robin Config", callback_data="rr_menu")
        ],
        [
            InlineKeyboardButton("💻 Opencode CLI Manager", callback_data="cli_tools_menu"),
            InlineKeyboardButton("➕ Add New Provider", callback_data="add_provider_menu")
        ]
    ])

def get_back_button(callback_data="view_quota"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Return to Dashboard", callback_data=callback_data)]])
