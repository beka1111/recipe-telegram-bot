import os
import requests
from bs4 import BeautifulSoup
import trafilatura
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Безопасное получение токена из настроек Render
TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Отправь мне ссылку на рецепт, и я постараюсь извлечь из неё чистый текст."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    
    if not url.startswith("http://") and not url.startswith("https://"):
        await update.message.reply_text("Пожалуйста, отправьте корректную ссылку.")
        return

    await update.message.reply_text("Скачиваю рецепт...")

    try:
        # Извлечение текста с помощью trafilatura
        downloaded = trafilatura.fetch_url(url)
        extracted_text = trafilatura.extract(downloaded)

        if extracted_text:
            # Если текст слишком длинный, режем на части для Telegram (лимит 4096 символов)
            if len(extracted_text) > 4000:
                for i in range(0, len(extracted_text), 4000):
                    await update.message.reply_text(extracted_text[i:i+4000])
            else:
                await update.message.reply_text(extracted_text)
        else:
            await update.message.reply_text("Не удалось извлечь текст рецепта из этой ссылки.")
            
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при обработке: {e}")

def main():
    if not TOKEN:
        print("ОШИБКА: Токен BOT_TOKEN не найден в переменных окружения!")
        return

    # Создание приложения
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота (с автоматической очисткой старых зависших сообщений drop_pending_updates=True)
    print("Бот успешно запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
