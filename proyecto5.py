#!/usr/bin/env python3
"""
Bot de Telegram Bilingüe Profesional
Desarrollado por: Ignacio Barberis
Versión: 2.0
Soporte: Español e Inglés
"""

import logging
import os
import sqlite3
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv

# Configuración
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Base de datos
def init_db():
    """Inicializar base de datos SQLite"""
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            language TEXT DEFAULT 'español',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_user(user_id, username, first_name, language='español'):
    """Guardar usuario en base de datos"""
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, language, last_active)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, language, datetime.now()))
    conn.commit()
    conn.close()

def get_user_language(user_id):
    """Obtener idioma del usuario"""
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'español'

# Mensajes bilingües
MESSAGES = {
    'español': {
        'welcome': '¡Hola {name}! 👋\n\nSoy tu bot asistente bilingüe. Puedo ayudarte con:\n\n🔹 Información general\n🔹 Soporte técnico\n🔹 Cambiar idioma\n🔹 Y mucho más!\n\nUsa los botones de abajo o escribe /help para ver todos los comandos.',
        'help': '📋 *COMANDOS DISPONIBLES:*\n\n/start - Iniciar bot\n/help - Mostrar ayuda\n/idioma - Cambiar idioma\n/info - Información del bot\n/contacto - Datos de contacto\n/productos - Nuestros servicios\n/soporte - Obtener soporte\n/stats - Estadísticas\n\n¿En qué puedo ayudarte?',
        'language_changed': '✅ Idioma cambiado a Español\n\n¡Perfecto! Ahora te responderé en español.',
        'info': '🤖 *INFORMACIÓN DEL BOT*\n\nVersión: 2.0\nDesarrollado por: Ignacio Barberis\nSoporte: Español e Inglés\nFunciones: Más de 10 comandos\n\n🔧 Bot profesional para empresas',
        'contact': '📞 *CONTACTO*\n\n📧 Email: tu@email.com\n💼 LinkedIn: /in/ignacio-barberis\n🐱 GitHub: @IgnacioBarberis\n🌐 Web: tu-portfolio.com\n\n⚡ Respuesta en menos de 24h',
        'products': '💼 *NUESTROS SERVICIOS*\n\n🤖 Bots personalizados\n🕷️ Web scraping\n📧 Automatización emails\n📊 Dashboards con IA\n💰 Apps financieras\n\n💵 Desde $50 - ¡Cotiza gratis!',
        'support': '🆘 *SOPORTE TÉCNICO*\n\nDescribe tu consulta y te ayudaré:\n\n1️⃣ Problemas técnicos\n2️⃣ Dudas sobre servicios\n3️⃣ Cotizaciones\n4️⃣ Personalización\n\nEscribe tu consulta...',
        'stats': '📊 *ESTADÍSTICAS*\n\nBot activo desde: {date}\nUsuarios registrados: {users}\nIdioma actual: Español\nÚltima actualización: {update}\n\n✅ Sistema funcionando correctamente',
        'unknown': '❓ No entiendo ese comando.\n\nUsa /help para ver comandos disponibles o utiliza los botones del menú.'
    },
    'english': {
        'welcome': 'Hello {name}! 👋\n\nI\'m your bilingual assistant bot. I can help you with:\n\n🔹 General information\n🔹 Technical support\n🔹 Language switching\n🔹 And much more!\n\nUse the buttons below or type /help to see all commands.',
        'help': '📋 *AVAILABLE COMMANDS:*\n\n/start - Start bot\n/help - Show help\n/idioma - Change language\n/info - Bot information\n/contacto - Contact info\n/productos - Our services\n/soporte - Get support\n/stats - Statistics\n\nHow can I help you?',
        'language_changed': '✅ Language changed to English\n\nPerfect! I\'ll now respond in English.',
        'info': '🤖 *BOT INFORMATION*\n\nVersion: 2.0\nDeveloped by: Ignacio Barberis\nSupport: Spanish & English\nFeatures: 10+ commands\n\n🔧 Professional bot for businesses',
        'contact': '📞 *CONTACT*\n\n📧 Email: tu@email.com\n💼 LinkedIn: /in/ignacio-barberis\n🐱 GitHub: @IgnacioBarberis\n🌐 Web: tu-portfolio.com\n\n⚡ Response in less than 24h',
        'products': '💼 *OUR SERVICES*\n\n🤖 Custom bots\n🕷️ Web scraping\n📧 Email automation\n📊 AI dashboards\n💰 Financial apps\n\n💵 From $50 - Free quote!',
        'support': '🆘 *TECHNICAL SUPPORT*\n\nDescribe your inquiry and I\'ll help:\n\n1️⃣ Technical issues\n2️⃣ Service questions\n3️⃣ Quotes\n4️⃣ Customization\n\nWrite your inquiry...',
        'stats': '📊 *STATISTICS*\n\nBot active since: {date}\nRegistered users: {users}\nCurrent language: English\nLast update: {update}\n\n✅ System working correctly',
        'unknown': '❓ I don\'t understand that command.\n\nUse /help to see available commands or use the menu buttons.'
    }
}

# Teclados
def get_main_keyboard(language):
    """Crear teclado principal según idioma"""
    if language == 'español':
        keyboard = [
            [KeyboardButton("ℹ️ Información"), KeyboardButton("📞 Contacto")],
            [KeyboardButton("💼 Servicios"), KeyboardButton("🆘 Soporte")],
            [KeyboardButton("🌐 Cambiar idioma"), KeyboardButton("📊 Estadísticas")]
        ]
    else:
        keyboard = [
            [KeyboardButton("ℹ️ Information"), KeyboardButton("📞 Contact")],
            [KeyboardButton("💼 Services"), KeyboardButton("🆘 Support")],
            [KeyboardButton("🌐 Change language"), KeyboardButton("📊 Statistics")]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Handlers
async def start(update: Update, context: CallbackContext):
    """Comando /start"""
    user = update.effective_user
    user_id = user.id
    username = user.username or "Sin username"
    first_name = user.first_name or "Usuario"
    
    # Detectar idioma inicial
    language = 'english' if context.args and 'english' in ' '.join(context.args).lower() else 'español'
    
    # Guardar usuario
    save_user(user_id, username, first_name, language)
    
    # Enviar mensaje de bienvenida
    message = MESSAGES[language]['welcome'].format(name=first_name)
    keyboard = get_main_keyboard(language)
    
    await update.message.reply_text(message, reply_markup=keyboard, parse_mode='Markdown')
    logger.info(f"Usuario {username} ({user_id}) inició el bot en {language}")

async def help_command(update: Update, context: CallbackContext):
    """Comando /help"""
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    
    message = MESSAGES[language]['help']
    await update.message.reply_text(message, parse_mode='Markdown')

async def change_language(update: Update, context: CallbackContext):
    """Comando /idioma"""
    user_id = update.effective_user.id
    current_language = get_user_language(user_id)
    
    # Cambiar idioma
    new_language = 'english' if current_language == 'español' else 'español'
    
    # Actualizar en base de datos
    save_user(user_id, update.effective_user.username, update.effective_user.first_name, new_language)
    
    # Enviar confirmación
    message = MESSAGES[new_language]['language_changed']
    keyboard = get_main_keyboard(new_language)
    
    await update.message.reply_text(message, reply_markup=keyboard)
    logger.info(f"Usuario {user_id} cambió idioma a {new_language}")

async def info_command(update: Update, context: CallbackContext):
    """Comando /info"""
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    
    message = MESSAGES[language]['info']
    await update.message.reply_text(message, parse_mode='Markdown')

async def contact_command(update: Update, context: CallbackContext):
    """Comando /contacto"""
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    
    message = MESSAGES[language]['contact']
    await update.message.reply_text(message, parse_mode='Markdown')

async def products_command(update: Update, context: CallbackContext):
    """Comando /productos"""
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    
    message = MESSAGES[language]['products']
    await update.message.reply_text(message, parse_mode='Markdown')

async def support_command(update: Update, context: CallbackContext):
    """Comando /soporte"""
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    
    message = MESSAGES[language]['support']
    await update.message.reply_text(message, parse_mode='Markdown')

async def stats_command(update: Update, context: CallbackContext):
    """Comando /stats"""
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    
    # Obtener estadísticas
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    conn.close()
    
    message = MESSAGES[language]['stats'].format(
        date="Julio 2025",
        users=user_count,
        update="17/07/2025"
    )
    await update.message.reply_text(message, parse_mode='Markdown')

async def handle_buttons(update: Update, context: CallbackContext):
    """Manejar botones del teclado"""
    user_id = update.effective_user.id
    language = get_user_language(user_id)
    text = update.message.text
    
    # Mapear botones a comandos
    button_mapping = {
        'ℹ️ Información': info_command,
        'ℹ️ Information': info_command,
        '📞 Contacto': contact_command,
        '📞 Contact': contact_command,
        '💼 Servicios': products_command,
        '💼 Services': products_command,
        '🆘 Soporte': support_command,
        '🆘 Support': support_command,
        '🌐 Cambiar idioma': change_language,
        '🌐 Change language': change_language,
        '📊 Estadísticas': stats_command,
        '📊 Statistics': stats_command
    }
    
    handler = button_mapping.get(text)
    if handler:
        await handler(update, context)
    else:
        # Mensaje no reconocido
        message = MESSAGES[language]['unknown']
        await update.message.reply_text(message)

async def error_handler(update: Update, context: CallbackContext):
    """Manejar errores"""
    logger.error(f"Error: {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "❌ Ha ocurrido un error. Por favor, inténtalo de nuevo.\n"
            "❌ An error occurred. Please try again."
        )

def main():
    """Función principal"""
    if not TOKEN:
        logger.error("ERROR: TELEGRAM_TOKEN no encontrado en variables de entorno")
        return
    
    # Inicializar base de datos
    init_db()
    logger.info("Base de datos inicializada")
    
    # Crear aplicación
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Agregar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("idioma", change_language))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("contacto", contact_command))
    application.add_handler(CommandHandler("productos", products_command))
    application.add_handler(CommandHandler("soporte", support_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Handler para botones
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    
    # Handler de errores
    application.add_error_handler(error_handler)
    
    # Iniciar bot
    logger.info("Bot iniciado correctamente")
    print("🤖 Bot de Telegram iniciado...")
    print("📱 Presiona Ctrl+C para detener")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
