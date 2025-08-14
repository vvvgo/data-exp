"""
Основной модуль Telegram бота
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from src.core.config import Config
from src.core.simple_chat_manager import SimpleChatManager
from src.bot.simple_handlers import SimpleHandlers

logger = logging.getLogger(__name__)


class ITMOChatBot:
    """Основной класс Telegram бота"""

    def __init__(self):
        # Проверяем конфигурацию
        Config.validate()

        self.chat_manager = SimpleChatManager()
        self.handlers = SimpleHandlers(self.chat_manager)

        # Создаем приложение бота
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

        # Регистрируем обработчики
        self._register_handlers()

        logger.info("ITMOChatBot инициализирован")

    def _register_handlers(self):
        """Регистрирует обработчики команд и сообщений"""
        app = self.application

        # Команды
        app.add_handler(CommandHandler("start", self.handlers.start_command))
        app.add_handler(CommandHandler("help", self.handlers.help_command))

        # Текстовые сообщения
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_message))

        # Обработчик ошибок
        app.add_error_handler(self.handlers.error_handler)

        logger.info("Обработчики зарегистрированы")

    def run(self):
        """Запускает бота"""
        logger.info("Запуск ИТМО чат-бота...")
        print("ИТМО чат-бот запущен!")
        print("Бот готов к работе в Telegram")

        # Запускаем polling
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
