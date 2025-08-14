"""
Основной менеджер чата
"""
import logging
from typing import Dict, Any, Optional

from src.knowledge.data_loader import DataLoader
from src.llm.response_generator import ResponseGenerator
from src.core.context_manager import ContextManager
from src.recommendations.recommendations import RecommendationEngine

logger = logging.getLogger(__name__)


class ChatManager:
    """Координирует работу всех компонентов чат-бота"""

    def __init__(self):
        self.data_loader = DataLoader()
        self.response_generator = ResponseGenerator()
        self.context_manager = ContextManager()
        self.recommendation_engine = RecommendationEngine()

        logger.info("ChatManager инициализирован")

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
            # Получаем контекст пользователя
            user_context = self.context_manager.get_user_context(user_id)

            # Проверяем релевантность вопроса
            if not self.response_generator.is_relevant_question(message):
                return self._get_irrelevant_response()

            # Определяем тип запроса
            query_type = self._classify_query(message)

            # Обрабатываем в зависимости от типа
            if query_type == "comparison":
                response = self._handle_comparison_request(message, user_context)
            elif query_type == "recommendations":
                response = self._handle_recommendation_request(message, user_context)
            else:
                response = self._handle_info_request(message, user_context)

            # Сохраняем в контекст
            self.context_manager.add_message(user_id, message, response)

            return response

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            return "Извините, произошла ошибка. Попробуйте задать вопрос еще раз."

    def _classify_query(self, message: str) -> str:
        """Классифицирует тип запроса"""
        message_lower = message.lower()

        comparison_keywords = ["сравни", "различия", "чем отличается", "что лучше", "выбрать"]
        recommendation_keywords = ["рекомендации", "дисциплины", "предметы", "что изучать", "посоветуй", "советы", "рекомендуй",
                                   "подходит", "программу выбрать", "какую программу", "дисциплин", "курсы", "обучение", "изучать", "предложи", "подскажи"]

        if any(keyword in message_lower for keyword in comparison_keywords):
            return "comparison"
        elif any(keyword in message_lower for keyword in recommendation_keywords):
            return "recommendations"
        else:
            return "info"

    def _handle_info_request(self, message: str, user_context: Dict) -> str:
        """Обрабатывает информационный запрос"""
        # Проверяем контекстные запросы (когда пользователь ссылается на предыдущее сообщение)
        context_indicators = ["это", "эта", "этой", "сколько это", "а сколько", "и сколько", "цена", "стоит"]
        message_lower = message.lower()

        # Если запрос контекстный и есть история
        if (any(indicator in message_lower for indicator in context_indicators) and
                user_context.get('history')):

            # Берем последнее сообщение пользователя для контекста
            last_user_message = ""
            for msg in reversed(user_context['history']):
                if msg.get('question'):
                    last_user_message = msg['question']
                    break

            # Расширяем запрос контекстом
            expanded_query = f"{last_user_message} {message}"
            context_data = self._search_relevant_info(expanded_query)
        else:
            # Обычный поиск
            context_data = self._search_relevant_info(message)

        # Генерируем ответ
        response = self.response_generator.generate_answer(
            user_question=message,
            context_data=context_data,
            user_background=user_context.get('background'),
            conversation_history=user_context.get('history', [])
        )

        return response

    def _handle_comparison_request(self, message: str, user_context: Dict) -> str:
        """Обрабатывает запрос сравнения программ"""
        # Получаем данные обеих программ
        all_programs = self.data_loader.get_all_programs()

        # Используем специальный промпт для сравнения
        response = self.response_generator.generate_answer(
            user_question=message,
            context_data=all_programs,
            user_background=user_context.get('background'),
            conversation_history=user_context.get('history', [])
        )

        return response

    def _handle_recommendation_request(self, message: str, user_context: Dict) -> str:
        """Обрабатывает запрос рекомендаций"""
        background = user_context.get('background', '')
        interests = user_context.get('interests', [])

        # Если нет информации о пользователе, запрашиваем
        if not background:
            return self._request_user_background()

        # Анализируем бэкграунд пользователя
        user_analysis = self.recommendation_engine.analyze_background(background)

        # Получаем данные программ
        all_programs = self.data_loader.get_all_programs()

        # Генерируем рекомендации
        program_recommendations = self.recommendation_engine.get_program_recommendations(
            user_analysis, all_programs
        )

        # Форматируем ответ
        return self._format_recommendations_response(program_recommendations)

    def _format_recommendations_response(self, recommendations: Dict) -> str:
        """Форматирует ответ с рекомендациями"""
        response_parts = ["**Персональные рекомендации:**\n"]

        for program_name, rec_data in recommendations.items():
            response_parts.append(f"**{program_name}** - {rec_data['suitability']}")
            response_parts.append(f"*Обоснование:* {rec_data['reasoning']}\n")

            if rec_data['recommended_subjects']:
                response_parts.append("*Рекомендуемые дисциплины:*")
                for subject in rec_data['recommended_subjects'][:3]:  # Топ 3
                    response_parts.append(f"• {subject['subject']} - {subject['reasoning']}")
                response_parts.append("")

        response_parts.append("Хотите узнать больше о какой-то конкретной программе?")
        return "\n".join(response_parts)

    def _search_relevant_info(self, query: str) -> Dict[str, Any]:
        """Ищет релевантную информацию по запросу с использованием RAG"""
        relevant_data = {}

        # Семантический поиск через RAG
        search_results = self.data_loader.semantic_search(query, top_k=5)

        if search_results:
            # Группируем результаты по программам
            for content, relevance, metadata in search_results:
                program_name = metadata.get('program', 'Неизвестная программа')
                section = metadata.get('section', 'Общая информация')

                if program_name not in relevant_data:
                    relevant_data[program_name] = {}

                relevant_data[program_name][f"{section} (релевантность: {relevance:.2f})"] = content
        else:
            # Fallback к простому поиску
            logger.warning("RAG поиск не дал результатов, используем простой поиск")
            for program_id in ["ai", "ai_product"]:
                program_data = self.data_loader.get_program_data(program_id)
                if program_data:
                    search_results = self.data_loader.search_in_program(program_id, query)
                    if search_results:
                        program_name = program_data.get('Направление образования', f'Программа {program_id}')
                        relevant_data[program_name] = search_results

        return relevant_data

    def _get_irrelevant_response(self) -> str:
        """Возвращает ответ на нерелевантный вопрос"""
        return """Извините, я специализируюсь только на вопросах о магистерских программах ИТМО в области искусственного интеллекта:

• **"Искусственный интеллект"** 
• **"Управление ИИ-продуктами"**

Я могу помочь с:
• Выбором программы под ваш бэкграунд
• Информацией о поступлении и обучении  
• Сравнением программ
• Рекомендациями по дисциплинам
• Карьерными возможностями

Задайте вопрос о магистерских программах ИТМО!"""

    def _request_user_background(self) -> str:
        """Запрашивает информацию о бэкграунде пользователя"""
        return """Чтобы дать персональные рекомендации по дисциплинам, расскажите о себе:

**Ваш бэкграунд:**
• Текущее образование/опыт работы
• Знакомство с программированием и ИИ
• Профессиональные интересы
• Планы на будущее

**Например:** "Я программист с опытом 2 года, работаю с Python, интересуюсь машинным обучением и хочу стать ML-инженером"

После этого я смогу предложить конкретные дисциплины!"""

    def set_user_background(self, user_id: str, background: str, interests: list = None) -> str:
        """Сохраняет информацию о пользователе"""
        self.context_manager.update_user_info(user_id, background, interests or [])
        return "Спасибо! Информация сохранена. Теперь можете запросить рекомендации по дисциплинам."

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Возвращает контекст пользователя"""
        return self.context_manager.get_user_context(user_id)
