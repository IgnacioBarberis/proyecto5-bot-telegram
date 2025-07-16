import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Mensajes predefinidos bilingües
mensajes = {
    "español": "¡Hola desde mi bot Telegram! Prueba en español. #BotBilingue",
    "inglés": "Hello from my Telegram bot! Test in English. #BilingualBot"
}

async def start(update: Update, context: CallbackContext):
    idioma = 'inglés' if 'english' in update.message.text.lower() else 'español'
    mensaje = mensajes.get(idioma, "Idioma no soportado")
    await update.message.reply_text(mensaje)

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == '__main__':
    main()