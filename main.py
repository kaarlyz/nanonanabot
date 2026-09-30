from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from config.settings import BOT_TOKEN
from handlers.dashboard_handlers import (
    start_command,
    button_callback_handler,
    start_add_wizard,
    wizard_oauth_step,
    wizard_name_step,
    wizard_key_step,
    wizard_url_step,
    cancel_wizard,
    ADD_OAUTH_CALLBACK,
    ADD_NAME,
    ADD_KEY,
    ADD_URL,
)


async def auto_healthcheck_job(context):
    from services.router_service import check_router_service_health, get_cooldown_accounts_count
    from config.settings import ADMIN_USER_ID
    if not ADMIN_USER_ID:
        return
    try:
        is_healthy, status_str = check_router_service_health()
        if not is_healthy:
            alert_text = f"🚨 <b>[9Router Offline Alert]</b>\nStatus: <b>{status_str}</b>\nPastikan service 9router di localhost aktif!"
            await context.bot.send_message(chat_id=int(ADMIN_USER_ID), text=alert_text, parse_mode="HTML")
            return

        total, bad_count, bad_accounts = get_cooldown_accounts_count()
        if bad_count > 0:
            alert_text = f"⚠️ <b>[9Router Cooldown Alert]</b>\nTerdeteksi <b>{bad_count}/{total}</b> akun bermasalah/cooldown:\n"
            for acc in bad_accounts[:5]:
                name = acc.get("name") or acc.get("email") or "Akun"
                err = acc.get("error") or "Cooldown 403"
                alert_text += f"• <code>{name}</code>: {err}\n"
            alert_text += "\n<i>Gunakan tombol '🩺 Healthcheck & Reset 403' di dashboard untuk unfreeze.</i>"
            await context.bot.send_message(chat_id=int(ADMIN_USER_ID), text=alert_text, parse_mode="HTML")
    except Exception as e:
        print(f"Auto-healthcheck job error: {e}")

def main():
    print("🚀 Initializing 9Router Professional Enterprise Bot...")
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
    
    # Commands
    app.add_handler(CommandHandler(["start", "dashboard", "quota", "token", "usage"], start_command))
    app.add_handler(wizard_handler)
    app.add_handler(CallbackQueryHandler(button_callback_handler))
    
    # Scheduled Background Healthcheck (every 30 mins)
    if app.job_queue:
        app.job_queue.run_repeating(auto_healthcheck_job, interval=1800, first=60)
    
    print("⚡ 9Router Enterprise Telegram Service is now online and polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
