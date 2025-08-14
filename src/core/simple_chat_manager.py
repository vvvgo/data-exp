"""
Упрощённый менеджер чата - только основные функции
"""
import logging

from src.knowledge.data_loader import DataLoader
from src.llm.response_generator import ResponseGenerator
from src.recommendations.recommendations import RecommendationEngine

logger = logging.getLogger(__name__)


class SimpleChatManager:
    """Простой менеджер чата с базовым функционалом"""

    def __init__(self):
        self.data_loader = DataLoader()
        self.response_generator = ResponseGenerator()
        self.recommendation_engine = RecommendationEngine()

        # Простое хранилище бэкграундов пользователей
        self.user_backgrounds = {}

        logger.info("SimpleChatManager инициализирован")

    def handle_message(self, user_id: str, message: str) -> str:
        """
        Обрабатывает сообщение пользователя

        Args:
            user_id: ID пользователя
            message: Текст сообщения

        Returns:
            Ответ бота
        """
        try:
            # Проверяем релевантность вопроса
            if not self.response_generator.is_relevant_question(message):
                return "Я отвечаю только на вопросы о магистерских программах ИТМО по ИИ и управлению ИИ-продуктами. Задайте вопрос по этой теме."

            # Простая проверка - это запрос рекомендаций?
            if self._is_recommendation_request(message):
                return self._handle_recommendations(user_id, message)
            else:
                return self._handle_question(message)

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            return "Извините, произошла ошибка. Попробуйте еще раз."

    def _is_recommendation_request(self, message: str) -> bool:
        """Проверяет, является ли сообщение запросом рекомендаций"""
        message_lower = message.lower()
        recommendation_keywords = [
            "рекомендаци", "посоветуй", "подскажи", "какую программу",
            "что выбрать", "что изучать", "мой бэкграунд", "мой опыт",
            "рекомендуй", "подходит", "советы"
        ]

        return any(keyword in message_lower for keyword in recommendation_keywords)

    def _handle_recommendations(self, user_id: str, message: str) -> str:
        """Обрабатывает запрос рекомендаций"""

        # Сохраняем бэкграунд пользователя если он есть в сообщении
        self.user_backgrounds[user_id] = message

        # Анализируем бэкграунд
        user_analysis = self.recommendation_engine.analyze_background(message)

        # Получаем данные программ
        all_programs = self.data_loader.get_all_programs()

        # Генерируем рекомендации
        recommendations = self.recommendation_engine.get_program_recommendations(
            user_analysis, all_programs
        )

        # Форматируем ответ
        return self._format_recommendations(recommendations)

    def _handle_question(self, message: str) -> str:
        """Обрабатывает обычный вопрос"""

        # Ищем релевантную информацию через RAG
        relevant_data = self.data_loader.semantic_search(message, top_k=3)

        if not relevant_data:
            return "Извините, я не нашёл информации по вашему вопросу. Попробуйте переформулировать."

        # Генерируем ответ через LLM
        return self.response_generator.generate_answer(
            user_question=message,
            context_data=self._format_context(relevant_data)
        )

    def _format_context(self, search_results) -> dict:
        """Форматирует результаты поиска для LLM"""
        context = {}

        for content, relevance, metadata in search_results:
            program = metadata.get('program', 'Общая информация')
            section = metadata.get('section', 'Основная информация')

            if program not in context:
                context[program] = {}

            context[program][f"{section} (релевантность: {relevance:.2f})"] = content

        return context

    def _format_recommendations(self, recommendations: dict) -> str:
        """Форматирует рекомендации"""
        response_parts = ["**Персональные рекомендации:**\n"]

        for program_name, rec_data in recommendations.items():
            response_parts.append(f"**{program_name}** - {rec_data['suitability']}")
            response_parts.append(f"*Обоснование:* {rec_data['reasoning']}\n")

            if rec_data['recommended_subjects']:
                response_parts.append("*Топ рекомендуемые дисциплины:*")
                for subject in rec_data['recommended_subjects'][:3]:  # Топ 3
                    response_parts.append(f"• {subject['subject']} - {subject['reasoning']}")
                response_parts.append("")

        return "\n".join(response_parts)

    def set_user_background(self, user_id: str, background: str):
        """Сохраняет бэкграунд пользователя"""
        self.user_backgrounds[user_id] = background
