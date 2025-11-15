from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)


ADMIN_ID = 7664056927  # ← Твой Telegram ID

pending_replies = {}
dialog_status = {}
chat_history = {}


# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_name = user.first_name if user.first_name else "пользователь"

    await update.message.reply_text(
        f"Здравствуйте, {first_name}!\n\n"
        f"Напишите ваш вопрос и я передам его администратору. "
        f"Он ответит вам в ближайшее время!"
    )


# --- Сообщения ---
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text

    # --- Админ ---
    if user.id == ADMIN_ID:
        if ADMIN_ID in pending_replies:
            client_id = pending_replies[ADMIN_ID]
            answer_text = message_text
            chat_history.setdefault(client_id, []).append(f"Админ: {answer_text}")

            await context.bot.send_message(
                chat_id=client_id,
                text=f"👨‍💻 Сообщение от администратора:\n\n{answer_text}"
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("↪️ Закрыть диалог", callback_data=f"close_{client_id}")],
                [InlineKeyboardButton("📜 История диалога", callback_data=f"history_{client_id}")]
            ])

            await update.message.reply_text(
                "✅ Сообщение успешно отправлено",
                reply_markup=keyboard
            )

            dialog_status[client_id] = True
            del pending_replies[ADMIN_ID]
        return

    # --- Клиент ---
    client_id = user.id
    dialog_status[client_id] = True
    chat_history.setdefault(client_id, []).append(f"{user.first_name}: {message_text}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝Ответить", callback_data=f"reply_{client_id}")]
    ])

    txt = (
        f"📩 Новое сообщение!\n\n"
        f"👤 От: {user.first_name}\n"
        f"🔗 Username: @{user.username}\n"
        f"📝 Сообщение:\n{message_text}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=txt,
        reply_markup=keyboard
    )

    await update.message.reply_text(
        "✅ Сообщение успешно было передано, ожидайте ответа"
    )


# --- Кнопки ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("reply_"):
        client_id = int(data.split("_")[1])
        pending_replies[ADMIN_ID] = client_id
        dialog_status[client_id] = True
        await query.message.reply_text("👨‍💻 Напишите ваш ответ в чат и я передам его клиенту")

    elif data.startswith("close_"):
        client_id = int(data.split("_")[1])
        dialog_status[client_id] = False
        if ADMIN_ID in pending_replies and pending_replies[ADMIN_ID] == client_id:
            del pending_replies[ADMIN_ID]
        await query.message.reply_text("❌ Диалог с клиентом закрыт")

    elif data.startswith("history_"):
        client_id = int(data.split("_")[1])
        history = chat_history.get(client_id, [])
        text = "📭 История диалога пуста." if not history else "📜 История диалога:\n\n" + "\n".join(history)
        await query.message.reply_text(text)


def main():
    TOKEN = "8384976157:AAG3ZQTotp-JK47odRbcWsICmZp_kq274as"  # ← вставьте новый токен после ревока

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()