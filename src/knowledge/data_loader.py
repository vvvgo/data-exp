"""
Загрузчик данных о программах ИТМО
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

from src.core.config import Config

logger = logging.getLogger(__name__)


class DataLoader:
    """Загружает и предоставляет доступ к данным о программах"""

    def __init__(self):
        self.data = {}
        self.rag_engine = None
        self.load_all_data()
        self._initialize_rag()

    def load_all_data(self):
        """Загружает все данные о программах"""
        try:
            # Загружаем данные по каждой программе
            for program_id, program_name in Config.PROGRAMS.items():
                file_path = Config.JSON_DATA_PATH / f"{program_name}.json"
                if file_path.exists():
                    self.data[program_id] = self.load_program_data(file_path)
                    logger.info(f"Загружены данные программы: {program_name}")
                else:
                    logger.warning(f"Файл не найден: {file_path}")

        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")

    def load_program_data(self, file_path: Path) -> Dict[str, Any]:
        """Загружает данные одной программы"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки файла {file_path}: {e}")
            return {}

    def get_program_data(self, program_id: str) -> Dict[str, Any]:
        """Возвращает данные программы по ID"""
        return self.data.get(program_id, {})

    def get_all_programs(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает данные всех программ"""
        return self.data

    def get_program_description(self, program_id: str) -> str:
        """Возвращает описание программы"""
        program_data = self.get_program_data(program_id)
        return program_data.get('Описание программы', '')

    def get_program_career(self, program_id: str) -> str:
        """Возвращает информацию о карьере"""
        program_data = self.get_program_data(program_id)
        return program_data.get('Карьера', '')

    def get_program_faq(self, program_id: str) -> Dict[str, str]:
        """Возвращает FAQ программы"""
        program_data = self.get_program_data(program_id)
        return program_data.get('Вопросы и ответы', {})

    def get_program_pdf_content(self, program_id: str) -> str:
        """Возвращает содержимое PDF учебного плана"""
        program_data = self.get_program_data(program_id)
        pdf_docs = program_data.get('PDF_документы', {})
        return pdf_docs.get('учебный_план', '')

    def search_in_program(self, program_id: str, query: str) -> Dict[str, Any]:
        """Ищет информацию в данных программы"""
        program_data = self.get_program_data(program_id)
        results = {}

        query_lower = query.lower()

        # Поиск в разных разделах
        for section, content in program_data.items():
            if isinstance(content, str) and query_lower in content.lower():
                results[section] = content
            elif isinstance(content, dict):
                for key, value in content.items():
                    if isinstance(value, str) and query_lower in value.lower():
                        results[f"{section} - {key}"] = value

        return results

    def _initialize_rag(self):
        """Инициализирует RAG engine"""
        try:
            # Используем единый RAG движок
            from src.knowledge.rag import LightweightFAISSRAG
            self.rag_engine = LightweightFAISSRAG()
            if self.data:
                self.rag_engine.index_data(self.data)
                logger.info("RAG engine инициализирован и проиндексирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации RAG: {e}")
            self.rag_engine = None

    def semantic_search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict]]:
        """
        Семантический поиск с использованием RAG

        Args:
            query: Поисковый запрос
            top_k: Количество результатов

        Returns:
            Список (текст, релевантность, метаданные)
        """
        if self.rag_engine:
            return self.rag_engine.search(query, top_k)
        else:
            logger.warning("RAG engine не инициализирован, используем простой поиск")
            return self._fallback_search(query)

    def _fallback_search(self, query: str) -> List[Tuple[str, float, Dict]]:
        """Резервный простой поиск, если RAG недоступен"""
        results = []
        query_lower = query.lower()

        for program_id, data in self.data.items():
            program_name = Config.PROGRAMS.get(program_id, program_id)
            search_results = self.search_in_program(program_id, query)

            for section, content in search_results.items():
                if content:
                    relevance = query_lower.count(' ') + 1  # Простая оценка
                    results.append((
                        f"Программа: {program_name}\nРаздел: {section}\n{content[:500]}...",
                        0.5,  # Базовая релевантность
                        {'program': program_name, 'section': section, 'type': 'search'}
                    ))

        return results[:5]

    def get_program_context(self, program_name: str) -> List[Tuple[str, float, Dict]]:
        """Получает полный контекст программы через RAG"""
        if self.rag_engine:
            return self.rag_engine.get_program_context(program_name)
        else:
            # Fallback к простому получению данных
            for program_id, full_name in Config.PROGRAMS.items():
                if full_name == program_name:
                    data = self.get_program_data(program_id)
                    return [(str(data), 1.0, {'program': program_name, 'type': 'full_context'})]
            return []

    def get_rag_stats(self) -> Dict[str, Any]:
        """Возвращает статистику RAG"""
        if self.rag_engine and hasattr(self.rag_engine, 'get_stats'):
            return self.rag_engine.get_stats()
        else:
            return {'status': 'not_available'}

    def rebuild_rag_index(self):
        """Пересоздает RAG индекс"""
        if self.rag_engine and self.data:
            try:
                # Очищаем кэш если это FAISS
                if hasattr(self.rag_engine, 'clear_cache'):
                    self.rag_engine.clear_cache()

                # Переиндексируем
                self.rag_engine.index_data(self.data, force_reindex=True)
                logger.info("RAG индекс пересоздан")
                return True
            except Exception as e:
                logger.error(f"Ошибка пересоздания индекса: {e}")
                return False
        return False
