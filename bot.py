import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
user_counts = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("Click me", callback_data="click")]]
    await update.message.reply_text("Welcome! Click the button to increase your score.", reply_markup=InlineKeyboardMarkup(keyboard))

async def click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_counts[user_id] = user_counts.get(user_id, 0) + 1
    text = f"You clicked {user_counts[user_id]} times."
    keyboard = [[InlineKeyboardButton("Click me", callback_data="click")]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    count = user_counts.get(user_id, 0)
    await update.message.reply_text(f"Your score: {count}")

def main() -> None:
    application = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("score", score))
    application.add_handler(CallbackQueryHandler(click, pattern="click"))
    application.run_polling()

if __name__ == "__main__":
    main()