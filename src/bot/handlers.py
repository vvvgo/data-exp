"""
Обработчики команд и сообщений для Telegram бота
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class BotHandlers:
    """Обработчики команд и сообщений бота"""

    def __init__(self, chat_manager):
        self.chat_manager = chat_manager

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = str(update.effective_user.id)
        username = update.effective_user.first_name or "Абитуриент"

        welcome_message = f"""Привет, {username}!

Я чат-бот помощник для абитуриентов магистратуры ИТМО в области искусственного интеллекта.

Я помогу вам с:
• Выбором между программами "Искусственный интеллект" и "Управление ИИ-продуктами"
• Информацией о поступлении и обучении
• Рекомендациями по выборным дисциплинам
• Сравнением программ

Команды:
/programs - информация о программах
/background - указать свой бэкграунд для персональных рекомендаций  
/help - справка
/clear - очистить историю

Просто задайте любой вопрос о магистерских программах ИТМО!"""

        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """**Справка по использованию бота**

**Примеры вопросов:**
• "Чем отличаются программы?"
• "Какие требования для поступления?"
• "Посоветуй дисциплины для ML-инженера"
• "Сколько стоит обучение?"
• "Какие проекты делают студенты?"

**Команды:**
/programs - краткая информация о программах
/background - указать свой бэкграунд
/clear - очистить историю диалога

**Для лучших рекомендаций:**
Расскажите о своем образовании, опыте и интересах через команду /background или просто в сообщении.

У вас есть вопросы о магистратуре ИТМО?"""

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def programs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /programs"""
        programs_info = """**Магистерские программы ИТМО в области ИИ:**

**1. "Искусственный интеллект"**
• Фокус: ML Engineering, Data Science, AI Research
• Карьера: ML Engineer, Data Scientist, AI Researcher
• Места: 51 бюджет + 55 контракт
• Стоимость: 599,000 ₽/год

**2. "Управление ИИ-продуктами"**  
• Фокус: Product Management, AI Product Development
• Карьера: AI Product Manager, AI Analyst
• Места: 14 бюджет + 50 контракт
• Стоимость: 599,000 ₽/год

**Общие особенности:**
• Проектный подход с реальными компаниями
• Дистанционное обучение в вечернее время
• Возможность совмещать с работой
• Диплом государственного образца

Задайте любой вопрос для подробной информации!"""

        await update.message.reply_text(programs_info, parse_mode='Markdown')

    async def background_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /background"""
        background_prompt = """**Расскажите о своем бэкграунде для персональных рекомендаций:**

**Что важно указать:**
• Образование (какой факультет, специальность)
• Опыт работы (сфера, должность, стаж)
• Технические навыки (языки программирования, инструменты)
• Знакомство с ИИ/ML (курсы, проекты, опыт)
• Профессиональные интересы и цели

**Пример:**
"Окончил ВТУ по направлению информатика. Работаю backend-разработчиком на Python 2 года. Изучал курсы по ML на Coursera, делал pet-проект по анализу данных. Хочу стать ML-инженером и работать с большими данными."

После указания бэкграунда вы сможете получить персональные рекомендации по дисциплинам!"""

        await update.message.reply_text(background_prompt, parse_mode='Markdown')

    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /clear"""
        user_id = str(update.effective_user.id)

        self.chat_manager.context_manager.clear_user_history(user_id)

        await update.message.reply_text(
            "🧹 История диалога очищена!\n\n"
            "Теперь можете начать новый диалог. "
            "Если хотите получить персональные рекомендации, "
            "не забудьте указать свой бэкграунд командой /background"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        try:
            user_id = str(update.effective_user.id)
            message = update.message.text

            # Показываем, что бот "печатает"
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action='typing'
            )

            # Проверяем, указывает ли пользователь свой бэкграунд
            if self._is_background_message(message):
                interests = self._extract_interests(message)
                response = self.chat_manager.set_user_background(user_id, message, interests)
            else:
                # Обычная обработка сообщения
                response = self.chat_manager.handle_message(user_id, message)

            # Отправляем ответ
            await update.message.reply_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "Извините, произошла ошибка при обработке вашего сообщения. "
                "Попробуйте еще раз или обратитесь к разработчику."
            )

    def _is_background_message(self, message: str) -> bool:
        """Определяет, является ли сообщение описанием бэкграунда"""
        background_indicators = [
            "я работаю", "у меня опыт", "я изучал", "моя специальность",
            "я программист", "я разработчик", "окончил", "учился",
            "мой бэкграунд", "мое образование", "по образованию"
        ]

        message_lower = message.lower()
        return any(indicator in message_lower for indicator in background_indicators)

    def _extract_interests(self, message: str) -> list:
        """Извлекает интересы из сообщения пользователя"""
        interests = []
        interest_keywords = {
            "машинное обучение": ["машинное обучение", "ml", "machine learning"],
            "глубокое обучение": ["глубокое обучение", "deep learning", "нейронные сети"],
            "обработка данных": ["анализ данных", "data science", "данные"],
            "компьютерное зрение": ["компьютерное зрение", "computer vision", "cv"],
            "nlp": ["nlp", "обработка языка", "natural language"],
            "продуктовая разработка": ["продукт", "product", "менеджмент"]
        }

        message_lower = message.lower()
        for interest, keywords in interest_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                interests.append(interest)

        return interests

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Exception while handling an update: {context.error}")

        # Если это Update, отправляем сообщение об ошибке
        if isinstance(update, Update) and update.message:
            await update.message.reply_text(
                "Произошла техническая ошибка. Попробуйте еще раз через минуту."
            )
