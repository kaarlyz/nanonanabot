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
    
    print("⚡ 9Router Enterprise Telegram Service is now online and polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
