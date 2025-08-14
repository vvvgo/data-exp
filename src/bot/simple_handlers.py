"""
Упрощённые обработчики команд Telegram бота
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class SimpleHandlers:
    """Простые обработчики для Telegram бота"""

    def __init__(self, chat_manager):
        self.chat_manager = chat_manager

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        welcome_text = """Привет! 

Я помогу вам выбрать между двумя магистерскими программами ИТМО:
• **Искусственный интеллект**
• **Управление ИИ-продуктами**

**Что я умею:**
1. **Отвечать на вопросы** о программах, дисциплинах, требованиях
2. **Давать рекомендации** - расскажите о своём опыте и получите персональные советы

**Примеры вопросов:**
• "Расскажи о программе Искусственный интеллект"
• "Чем отличаются программы?"
• "Посоветуй мне программу - я программист с опытом в ML"

Задайте любой вопрос!"""

        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """**Как пользоваться ботом:**

**Вопросы о программах:**
• "Что изучают на программе ИИ?"
• "Какие требования для поступления?"
• "Сколько длится обучение?"

**Запрос рекомендаций:**
• "Посоветуй мне программу - у меня опыт в Python и ML"
• "Какую программу выбрать программисту?"
• "Рекомендации для менеджера продукта"

Просто напишите свой вопрос!"""

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        try:
            user_id = str(update.effective_user.id)
            message_text = update.message.text

            # Обрабатываем сообщение через чат-менеджер
            response = self.chat_manager.handle_message(user_id, message_text)

            await update.message.reply_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "Произошла техническая ошибка. Попробуйте еще раз через минуту."
            )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Ошибка бота: {context.error}")

        if update and update.message:
            try:
                await update.message.reply_text(
                    "Произошла техническая ошибка. Попробуйте еще раз."
                )
            except Exception:
                pass  # Игнорируем ошибки при отправке сообщения об ошибке
