"""
Генератор ответов с использованием OpenAI API
"""
import logging
from typing import Dict, Any, List
from openai import OpenAI

from src.core.config import Config
from src.llm.prompts import PromptTemplates

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Генерирует ответы пользователям с помощью OpenAI"""

    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.prompts = PromptTemplates()

    def generate_answer(self,
                        user_question: str,
                        context_data: Dict[str, Any],
                        user_background: str = None,
                        conversation_history: List[Dict] = None) -> str:
        """
        Генерирует ответ на вопрос пользователя

        Args:
            user_question: Вопрос пользователя
            context_data: Релевантные данные из базы знаний
            user_background: Информация о бэкграунде пользователя
            conversation_history: История предыдущих сообщений

        Returns:
            Сгенерированный ответ
        """
        try:
            # Формируем промпт
            system_prompt = self._build_system_prompt(context_data, user_background)
            user_prompt = self._build_user_prompt(user_question, conversation_history)

            # Запрос к OpenAI
            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE
            )

            answer = response.choices[0].message.content.strip()
            logger.info("Ответ успешно сгенерирован")
            return answer

        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return "Извините, произошла ошибка при генерации ответа. Попробуйте еще раз."

    def generate_recommendations(self,
                                 user_background: str,
                                 interests: List[str],
                                 program_data: Dict[str, Any]) -> str:
        """
        Генерирует персональные рекомендации по дисциплинам

        Args:
            user_background: Бэкграунд пользователя
            interests: Интересы пользователя
            program_data: Данные о программах

        Returns:
            Рекомендации по дисциплинам
        """
        try:
            system_prompt = self.prompts.get_recommendations_prompt()
            user_prompt = self.prompts.build_recommendations_query(
                user_background, interests, program_data
            )

            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE
            )

            recommendations = response.choices[0].message.content.strip()
            logger.info("Рекомендации успешно сгенерированы")
            return recommendations

        except Exception as e:
            logger.error(f"Ошибка генерации рекомендаций: {e}")
            return "Извините, произошла ошибка при генерации рекомендаций."

    def _build_system_prompt(self, context_data: Dict[str, Any], user_background: str = None) -> str:
        """Строит системный промпт"""
        base_prompt = self.prompts.get_base_system_prompt()

        # Добавляем контекстную информацию
        if context_data:
            context_text = self._format_context_data(context_data)
            base_prompt += f"\n\nДанные о программах ИТМО:\n{context_text}"

        # Добавляем информацию о пользователе
        if user_background:
            base_prompt += f"\n\nИнформация о пользователе: {user_background}"

        return base_prompt

    def _build_user_prompt(self, question: str, history: List[Dict] = None) -> str:
        """Строит пользовательский промпт"""
        prompt = f"Вопрос: {question}"

        if history:
            history_text = "\n".join([
                f"Пользователь: {msg.get('question', '')}\nБот: {msg.get('answer', '')}"
                for msg in history[-3:]  # Последние 3 сообщения
            ])
            prompt = f"История диалога:\n{history_text}\n\n{prompt}"

        return prompt

    def _format_context_data(self, context_data: Dict[str, Any]) -> str:
        """Форматирует данные контекста для промпта"""
        formatted_parts = []

        for section, content in context_data.items():
            if isinstance(content, str):
                formatted_parts.append(f"**{section}:**\n{content}\n")
            elif isinstance(content, dict):
                dict_content = "\n".join([f"- {k}: {v}" for k, v in content.items()])
                formatted_parts.append(f"**{section}:**\n{dict_content}\n")
            elif isinstance(content, list):
                list_content = "\n".join([f"- {item}" for item in content])
                formatted_parts.append(f"**{section}:**\n{list_content}\n")

        return "\n".join(formatted_parts)

    def is_relevant_question(self, question: str) -> bool:
        """
        Определяет, относится ли вопрос к магистерским программам ИТМО

        Args:
            question: Вопрос пользователя

        Returns:
            True если вопрос релевантный, False иначе
        """
        try:
            relevance_prompt = self.prompts.get_relevance_check_prompt()

            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": relevance_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=50,
                temperature=0.1
            )

            result = response.choices[0].message.content.strip().lower()
            return result.startswith("да") or result.startswith("yes")

        except Exception as e:
            logger.error(f"Ошибка проверки релевантности: {e}")
            return True  # В случае ошибки считаем вопрос релевантным
