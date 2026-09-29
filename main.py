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
    from services.router_service import trigger_batch_healthcheck, get_auth_token
    from config.settings import ADMIN_USER_ID
    if not ADMIN_USER_ID:
        return
    try:
        res = trigger_batch_healthcheck()
        cooldown_or_dead = [acc for acc in res.get("tested", []) if not acc.get("valid")]
        if cooldown_or_dead:
            text = f"⚠️ <b>[9Router Alert] Terdeteksi {len(cooldown_or_dead)} Akun Bermasalah:</b>\n"
            for acc in cooldown_or_dead[:5]:
                text += f"• <code>{acc.get('name', 'Acc')}</code>: {acc.get('error', 'Error/Cooldown')}\n"
            text += "\n<i>Silakan tekan tombol '🩺 Healthcheck & Reset 403' di bot untuk me-refresh.</i>"
            await context.bot.send_message(chat_id=int(ADMIN_USER_ID), text=text, parse_mode="HTML")
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
