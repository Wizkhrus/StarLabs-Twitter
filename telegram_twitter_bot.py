#!/usr/bin/env python3
"""
Simple Telegram to Twitter Bot
Простой бот для публикации сообщений из Telegram в Twitter

Требования:
pip install python-telegram-bot tweepy

Настройка:
1. Создайте бота через @BotFather и получите TELEGRAM_BOT_TOKEN
2. Получите Twitter API ключи на https://developer.twitter.com
3. Замените значения переменных ниже
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import tweepy
import os

# ============= НАСТРОЙКИ =============
# Telegram Bot Token от @BotFather
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

# Twitter API credentials
TWITTER_API_KEY = "YOUR_TWITTER_API_KEY"
TWITTER_API_SECRET = "YOUR_TWITTER_API_SECRET"
TWITTER_ACCESS_TOKEN = "YOUR_TWITTER_ACCESS_TOKEN"
TWITTER_ACCESS_TOKEN_SECRET = "YOUR_TWITTER_ACCESS_TOKEN_SECRET"

# Список разрешенных Telegram user IDs (для безопасности)
ALLOWED_USER_IDS = []  # Пример: [123456789, 987654321]
# =====================================

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Twitter API
try:
    twitter_auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    twitter_auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    twitter_api = tweepy.API(twitter_auth)
    twitter_client = tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
    )
    logger.info("Twitter API инициализирован")
except Exception as e:
    logger.error(f"Ошибка инициализации Twitter API: {e}")
    twitter_api = None
    twitter_client = None


def check_user_access(user_id: int) -> bool:
    """Проверка доступа пользователя"""
    if not ALLOWED_USER_IDS:
        return True  # Если список пуст, доступ всем
    return user_id in ALLOWED_USER_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start"""
    user = update.effective_user
    
    if not check_user_access(user.id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

🤖 Я бот для публикации сообщений в Twitter.

📝 Просто отправьте мне текст, и я опубликую его как твит.

📋 Доступные команды:
/start - Показать это сообщение
/help - Справка
/status - Проверить статус подключения

✉️ Отправьте любое текстовое сообщение для публикации в Twitter!
    """
    
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help"""
    if not check_user_access(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    help_text = """
📖 Справка:

1. Отправьте текстовое сообщение боту
2. Бот автоматически опубликует его в Twitter
3. Вы получите подтверждение с ссылкой на твит

⚠️ Ограничения:
- Максимум 280 символов для твита
- Бот публикует только текст (без изображений)

💡 Совет: Проверяйте текст перед отправкой!
    """
    
    await update.message.reply_text(help_text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /status - проверка подключения к Twitter"""
    if not check_user_access(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    await update.message.reply_text("⏳ Проверяю подключение к Twitter...")
    
    if not twitter_api or not twitter_client:
        await update.message.reply_text("❌ Twitter API не инициализирован. Проверьте настройки.")
        return
    
    try:
        me = twitter_api.verify_credentials()
        status_text = f"""
✅ Подключение к Twitter активно!

👤 Аккаунт: @{me.screen_name}
📝 Имя: {me.name}
📊 Твитов: {me.statuses_count}
👥 Подписчиков: {me.followers_count}
        """
        await update.message.reply_text(status_text)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка проверки: {str(e)}")


async def post_to_twitter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка текстовых сообщений и публикация в Twitter"""
    user = update.effective_user
    
    if not check_user_access(user.id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    if not twitter_client:
        await update.message.reply_text("❌ Twitter API не настроен. Обратитесь к администратору.")
        return
    
    tweet_text = update.message.text
    
    # Проверка длины твита
    if len(tweet_text) > 280:
        await update.message.reply_text(
            f"❌ Твит слишком длинный!\n\n"
            f"📏 Текущая длина: {len(tweet_text)} символов\n"
            f"📏 Максимум: 280 символов\n\n"
            f"✂️ Сократите текст на {len(tweet_text) - 280} символов."
        )
        return
    
    await update.message.reply_text("⏳ Публикую твит...")
    
    try:
        # Публикация твита
        response = twitter_client.create_tweet(text=tweet_text)
        tweet_id = response.data['id']
        
        # Получение информации о пользователе для формирования ссылки
        me = twitter_api.verify_credentials()
        tweet_url = f"https://twitter.com/{me.screen_name}/status/{tweet_id}"
        
        success_text = f"""
✅ Твит успешно опубликован!

🔗 Ссылка: {tweet_url}
📝 Текст: {tweet_text[:100]}{'...' if len(tweet_text) > 100 else ''}
        """
        
        await update.message.reply_text(success_text)
        logger.info(f"Пользователь {user.username} ({user.id}) опубликовал твит: {tweet_id}")
        
    except Exception as e:
        error_text = f"❌ Ошибка при публикации:\n{str(e)}"
        await update.message.reply_text(error_text)
        logger.error(f"Ошибка публикации твита: {e}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла ошибка при обработке вашего запроса.\n"
            "Попробуйте позже или обратитесь к администратору."
        )


def main() -> None:
    """Запуск бота"""
    # Проверка настроек
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error("❌ ОШИБКА: Не установлен TELEGRAM_BOT_TOKEN!")
        logger.error("Откройте файл и замените YOUR_TELEGRAM_BOT_TOKEN_HERE на ваш токен")
        return
    
    if TWITTER_API_KEY == "YOUR_TWITTER_API_KEY":
        logger.error("❌ ОШИБКА: Не установлены Twitter API credentials!")
        logger.error("Откройте файл и замените все YOUR_TWITTER_* на ваши ключи")
        return
    
    # Создание приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, post_to_twitter))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запуск бота
    logger.info("🚀 Бот запущен!")
    logger.info("📱 Отправьте /start для начала работы")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
