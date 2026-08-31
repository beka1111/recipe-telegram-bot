import logging
import requests
from io import BytesIO
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def extract_recipe(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    for element in soup(["script", "style", "aside", "nav", "footer", "header", "iframe", "form"]):
        element.extract()
        
    title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Рецепт"
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 20]
    recipe_text = "\n\n".join(paragraphs[:15])
    
    image_bytes = None
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src') or img.get('data-original')
        if src and not src.endswith('.svg') and 'icon' not in src and 'avatar' not in src:
            full_img_url = urljoin(url, src)
            try:
                img_res = requests.get(full_img_url, headers=headers, timeout=5)
                if img_res.status_code == 200 and len(img_res.content) > 5000:
                    image_bytes = BytesIO(img_res.content)
                    break
            except Exception:
                continue
            
    return title, recipe_text, image_bytes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Отправьте ссылку на рецепт, я очищу её от рекламы и загружу фото."
    )

async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http://") and not url.startswith("https://"):
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="Отправьте корректную ссылку (с http:// или https://)."
        )
        return

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Очищаю страницу и загружаю фото...")

    try:
        title, text, img_bytes = extract_recipe(url)
        caption = f"<b>{title}</b>\n\n{text}"
        
        if img_bytes:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id, 
                photo=img_bytes, 
                caption=caption[:1024], 
                parse_mode='HTML'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=caption[:4096], 
                parse_mode='HTML'
            )
            
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=f"Ошибка при обработке: {e}"
        )

if __name__ == '__main__':
    TOKEN = "8931441802:AAFMSsbpSE7m_aaY9PkrN7Z0O4hCr4LM6rk"
    
    # Добавлены параметры read_timeout и connect_timeout для стабильности соединения
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .read_timeout(30)
        .connect_timeout(30)
        .build()
    )
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), process_link))
    
    # Добавлен параметр drop_pending_updates, чтобы пропустить зависшие запросы
    application.run_polling(drop_pending_updates=True)
