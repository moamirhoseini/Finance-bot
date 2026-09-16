# -import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes,
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
logging.basicConfig(level=logging.INFO)

ASK_PRINCIPAL, ASK_RATE, ASK_YEARS = range(3)


def compound(principal, rate, years, n=12):
    return principal * (1 + rate / n) ** (n * years)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💰 ارزش آینده", callback_data="fv")]]
    await update.message.reply_text(
        "سلام! انتخاب کن:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def choose(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["mode"] = query.data
    await query.edit_message_text("💰 سرمایه اولیه:")
    return ASK_PRINCIPAL


async def get_principal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["principal"] = float(update.message.text.replace(",", ""))
    except ValueError:
        await update.message.reply_text("❌ عدد معتبر بفرست!")
        return ASK_PRINCIPAL
    await update.message.reply_text("📊 نرخ سود (مثلاً 0.18):")
    return ASK_RATE


async def get_rate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        v = float(update.message.text.replace(",", ""))
        v = v / 100 if v > 1 else v
    except ValueError:
        await update.message.reply_text("❌ عدد معتبر بفرست!")
        return ASK_RATE
    ctx.user_data["rate"] = v
    await update.message.reply_text("⏳ چند سال؟")
    return ASK_YEARS


async def get_years(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        years = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ عدد صحیح بفرست!")
        return ASK_YEARS

    d = ctx.user_data
    result = compound(d["principal"], d["rate"], years)
    await update.message.reply_text(
        f"✅ ارزش آینده: {result:,.0f} تومان\n"
        f"📈 سود: {result - d['principal']:,.0f} تومان"
    )
    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(choose, pattern="^fv$")],
        states={
            ASK_PRINCIPAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_principal)],
            ASK_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rate)],
            ASK_YEARS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_years)],
        },
        fallbacks=[],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    print("🤖 ربات روشن شد...")
    app.run_polling()


if __name__ == "__main__":
    main()