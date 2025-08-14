"""
Система рекомендаций дисциплин на основе бэкграунда пользователя
"""
import logging
import re
from typing import Dict, List, Any, Tuple
from collections import defaultdict

from src.core.config import Config

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Движок рекомендаций дисциплин"""

    def __init__(self):
        self.skill_keywords = {
            'programming': ['python', 'java', 'javascript', 'c++', 'программирование', 'разработка', 'код'],
            'ml': ['машинное обучение', 'ml', 'machine learning', 'нейронные сети', 'deep learning', 'sklearn'],
            'data_science': ['анализ данных', 'data science', 'pandas', 'numpy', 'статистика', 'данные'],
            'web_dev': ['веб', 'web', 'frontend', 'backend', 'django', 'flask', 'react'],
            'mobile': ['мобильная разработка', 'android', 'ios', 'flutter', 'react native'],
            'databases': ['база данных', 'sql', 'postgresql', 'mongodb', 'database'],
            'math': ['математика', 'алгебра', 'статистика', 'вероятность', 'алгоритмы'],
            'business': ['бизнес', 'менеджмент', 'управление', 'продукт', 'аналитика'],
            'ai_research': ['исследования', 'научная работа', 'публикации', 'конференции'],
            'computer_vision': ['компьютерное зрение', 'computer vision', 'opencv', 'изображения'],
            'nlp': ['nlp', 'обработка языка', 'natural language', 'текст'],
            'devops': ['devops', 'docker', 'kubernetes', 'ci/cd', 'инфраструктура']
        }

        self.career_paths = {
            'ml_engineer': {
                'keywords': ['ml engineer', 'ml-инженер', 'машинное обучение'],
                'skills': ['programming', 'ml', 'data_science', 'math'],
                'weight': 1.0
            },
            'data_scientist': {
                'keywords': ['data scientist', 'аналитик данных', 'исследователь данных'],
                'skills': ['data_science', 'ml', 'math', 'programming'],
                'weight': 1.0
            },
            'ai_product_manager': {
                'keywords': ['product manager', 'продуктовый менеджер', 'управление продуктом'],
                'skills': ['business', 'ml', 'data_science'],
                'weight': 1.0
            },
            'ai_researcher': {
                'keywords': ['исследователь', 'researcher', 'научная работа'],
                'skills': ['ai_research', 'ml', 'math', 'programming'],
                'weight': 1.0
            },
            'software_engineer': {
                'keywords': ['разработчик', 'программист', 'software engineer'],
                'skills': ['programming', 'web_dev', 'databases'],
                'weight': 0.8
            }
        }

        logger.info("RecommendationEngine инициализирован")

    def analyze_background(self, background_text: str) -> Dict[str, Any]:
        """
        Анализирует бэкграунд пользователя

        Args:
            background_text: Текст с описанием бэкграунда

        Returns:
            Анализ навыков и карьерных предпочтений
        """
        text_lower = background_text.lower()

        # Определяем навыки
        detected_skills = {}
        for skill_category, keywords in self.skill_keywords.items():
            skill_score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    skill_score += 1
            if skill_score > 0:
                detected_skills[skill_category] = skill_score / len(keywords)

        # Определяем карьерные цели
        career_scores = {}
        for career, info in self.career_paths.items():
            score = 0
            for keyword in info['keywords']:
                if keyword in text_lower:
                    score += 2  # Прямые упоминания карьеры весят больше

            # Добавляем баллы за релевантные навыки
            for skill in info['skills']:
                if skill in detected_skills:
                    score += detected_skills[skill] * info['weight']

            if score > 0:
                career_scores[career] = score

        # Определяем опыт работы
        experience_years = self._extract_experience(text_lower)

        # Определяем образование
        education_level = self._extract_education(text_lower)

        return {
            'skills': detected_skills,
            'career_goals': career_scores,
            'experience_years': experience_years,
            'education_level': education_level,
            'text': background_text
        }

    def _extract_experience(self, text: str) -> int:
        """Извлекает количество лет опыта"""
        patterns = [
            r'(\d+)\s*(?:лет|года|год)',
            r'опыт\s*(\d+)',
            r'работаю\s*(\d+)',
            r'(\d+)\s*years?'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        # Если нет точного числа, определяем по ключевым словам
        if any(word in text for word in ['junior', 'начинающий', 'студент']):
            return 0
        elif any(word in text for word in ['middle', 'опытный']):
            return 3
        elif any(word in text for word in ['senior', 'ведущий', 'старший']):
            return 5

        return 1  # По умолчанию

    def _extract_education(self, text: str) -> str:
        """Определяет уровень образования"""
        if any(word in text for word in ['магистр', 'кандидат', 'phd', 'аспирант']):
            return 'graduate'
        elif any(word in text for word in ['бакалавр', 'окончил', 'университет', 'институт']):
            return 'bachelor'
        else:
            return 'other'

    def get_program_recommendations(self, user_analysis: Dict[str, Any], curriculum_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Генерирует рекомендации программ и дисциплин

        Args:
            user_analysis: Результат анализа пользователя
            curriculum_data: Данные о программах с учебными планами

        Returns:
            Рекомендации по программам
        """
        recommendations = {}

        for program_id, program_name in Config.PROGRAMS.items():
            program_data = curriculum_data.get(program_id, {})

            # Оценка соответствия программы пользователю
            program_score = self._calculate_program_score(user_analysis, program_id)

            # Извлекаем дисциплины из учебного плана
            subjects = self._extract_subjects_from_curriculum(program_data)

            # Рекомендуем дисциплины
            subject_recommendations = self._recommend_subjects(user_analysis, subjects)

            recommendations[program_name] = {
                'program_score': program_score,
                'suitability': self._get_suitability_text(program_score),
                'recommended_subjects': subject_recommendations[:5],  # Топ 5
                'reasoning': self._generate_reasoning(user_analysis, program_id),
                'program_id': program_id
            }

        return recommendations

    def _calculate_program_score(self, user_analysis: Dict[str, Any], program_id: str) -> float:
        """Вычисляет оценку соответствия программы пользователю"""
        skills = user_analysis['skills']
        career_goals = user_analysis['career_goals']

        score = 0.0

        # Весовые коэффициенты для программ
        if program_id == 'ai':  # Искусственный интеллект
            # Больше подходит для технических ролей
            score += skills.get('programming', 0) * 0.3
            score += skills.get('ml', 0) * 0.4
            score += skills.get('math', 0) * 0.2
            score += skills.get('data_science', 0) * 0.3

            # Карьерные цели
            score += career_goals.get('ml_engineer', 0) * 0.4
            score += career_goals.get('data_scientist', 0) * 0.3
            score += career_goals.get('ai_researcher', 0) * 0.4

        elif program_id == 'ai_product':  # Управление ИИ-продуктами
            # Больше подходит для продуктовых ролей
            score += skills.get('business', 0) * 0.4
            score += skills.get('ml', 0) * 0.2
            score += skills.get('programming', 0) * 0.2
            score += skills.get('data_science', 0) * 0.2

            # Карьерные цели
            score += career_goals.get('ai_product_manager', 0) * 0.5
            score += career_goals.get('ml_engineer', 0) * 0.2

        # Нормализуем оценку
        return min(score, 1.0)

    def _extract_subjects_from_curriculum(self, program_data: Dict[str, Any]) -> List[str]:
        """Извлекает дисциплины из учебного плана"""
        subjects = []

        # Извлекаем из PDF контента
        pdf_content = program_data.get('PDF_документы', {}).get('учебный_план', '')
        if pdf_content:
            # Простой парсинг дисциплин (можно улучшить)
            lines = pdf_content.split('\n')
            for line in lines:
                line = line.strip()
                # Ищем строки, похожие на названия дисциплин
                if (len(line) > 10 and len(line) < 200 and
                    not line.isdigit() and
                        any(word in line.lower() for word in ['дисциплина', 'курс', 'анализ', 'обучение', 'технологии', 'системы', 'методы', 'машинное', 'данных', 'программирование', 'разработка', 'mlops', 'веб'])):

                    # Очищаем название от лишних цифр
                    cleaned_subject = self._clean_subject_name(line)
                    if cleaned_subject and len(cleaned_subject) > 5:
                        subjects.append(cleaned_subject)

        return subjects[:20]  # Ограничиваем количество

    def _clean_subject_name(self, subject: str) -> str:
        """Очищает название дисциплины от лишних цифр и кодов"""
        import re

        # Убираем номер семестра в начале (1, 2, 3 и т.д.)
        subject = re.sub(r'^\d+', '', subject)

        # Убираем коды в конце (3108, 6216 и т.д.)
        subject = re.sub(r'\s+\d{4,}$', '', subject)

        # Убираем лишние пробелы
        subject = subject.strip()

        return subject

    def _recommend_subjects(self, user_analysis: Dict[str, Any], subjects: List[str]) -> List[Dict]:
        """Рекомендует дисциплины на основе анализа пользователя"""
        recommendations = []

        skills = user_analysis['skills']
        career_goals = user_analysis['career_goals']

        for subject in subjects:
            subject_lower = subject.lower()
            relevance_score = 0.0
            reasoning = []

            # Анализируем соответствие навыкам
            if any(keyword in subject_lower for keyword in self.skill_keywords['ml']):
                if 'ml' in skills:
                    relevance_score += 0.4
                    reasoning.append("соответствует вашему опыту в ML")
                else:
                    relevance_score += 0.3
                    reasoning.append("поможет изучить машинное обучение")

            if any(keyword in subject_lower for keyword in self.skill_keywords['programming']):
                if 'programming' in skills:
                    relevance_score += 0.3
                    reasoning.append("развивает навыки программирования")

            if any(keyword in subject_lower for keyword in self.skill_keywords['data_science']):
                if 'data_science' in skills:
                    relevance_score += 0.3
                    reasoning.append("углубляет знания в анализе данных")

            if any(keyword in subject_lower for keyword in self.skill_keywords['business']):
                if 'business' in skills or 'ai_product_manager' in career_goals:
                    relevance_score += 0.4
                    reasoning.append("важно для продуктовых ролей")

            # Анализируем соответствие карьерным целям
            if 'ml_engineer' in career_goals and any(word in subject_lower for word in ['алгоритм', 'модел', 'нейрон']):
                relevance_score += 0.3
                reasoning.append("необходимо для ML-инженера")

            if 'ai_product_manager' in career_goals and any(word in subject_lower for word in ['продукт', 'управление', 'аналитика']):
                relevance_score += 0.3
                reasoning.append("важно для AI Product Manager")

            if relevance_score > 0.2:  # Минимальный порог
                recommendations.append({
                    'subject': subject,
                    'relevance_score': relevance_score,
                    'reasoning': ', '.join(reasoning) if reasoning else 'общее развитие в области ИИ'
                })

        # Сортируем по релевантности
        recommendations.sort(key=lambda x: x['relevance_score'], reverse=True)
        return recommendations

    def _get_suitability_text(self, score: float) -> str:
        """Преобразует числовую оценку в текстовое описание"""
        if score >= 0.7:
            return "отлично подходит"
        elif score >= 0.5:
            return "хорошо подходит"
        elif score >= 0.3:
            return "подходит с некоторыми условиями"
        else:
            return "требует дополнительной подготовки"

    def _generate_reasoning(self, user_analysis: Dict[str, Any], program_id: str) -> str:
        """Генерирует обоснование рекомендации"""
        skills = user_analysis['skills']
        career_goals = user_analysis['career_goals']
        experience = user_analysis['experience_years']

        reasons = []

        if program_id == 'ai':
            if 'ml' in skills:
                reasons.append("у вас есть опыт в машинном обучении")
            if 'programming' in skills:
                reasons.append("вы владеете программированием")
            if 'ml_engineer' in career_goals:
                reasons.append("соответствует вашей цели стать ML-инженером")
            if experience >= 2:
                reasons.append("ваш опыт позволяет успешно освоить программу")

        elif program_id == 'ai_product':
            if 'business' in skills:
                reasons.append("у вас есть понимание бизнес-процессов")
            if 'ai_product_manager' in career_goals:
                reasons.append("соответствует цели стать AI Product Manager")
            if 'ml' in skills or 'data_science' in skills:
                reasons.append("техническая база поможет в работе с командами разработки")

        if not reasons:
            reasons.append("программа поможет развить навыки в области ИИ")

        return "; ".join(reasons)
