"""
 FAISS RAG
"""
import logging
import numpy as np
import re
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
import math

logger = logging.getLogger(__name__)


class LightweightFAISSRAG:
    """ RAG с TF-IDF + FAISS"""

    def __init__(self):
        self.chunks = []
        self.metadata = []
        self.vocabulary = {}
        self.idf_weights = {}
        self.embeddings = None
        self.index = None

        try:
            import faiss
            self.faiss_available = True
            logger.info("FAISS доступен")
        except ImportError:
            self.faiss_available = False
            logger.warning("FAISS недоступен, используем простой поиск")

    def index_data(self, programs_data: Dict[str, Any], force_reindex: bool = False):
        """Индексирует данные с TF-IDF + FAISS"""
        try:
            from src.core.config import Config

            self.chunks = []
            self.metadata = []

            # Создаем чанки
            for program_id, data in programs_data.items():
                program_name = Config.PROGRAMS.get(program_id, program_id)
                chunks, metadata = self._create_chunks(data, program_name, program_id)
                self.chunks.extend(chunks)
                self.metadata.extend(metadata)

            logger.info(f"Создано {len(self.chunks)} чанков")

            if self.chunks:
                # Строим TF-IDF векторы
                self._build_tfidf_vectors()

                # Создаем FAISS индекс если доступен
                if self.faiss_available:
                    self._build_faiss_index()

                logger.info("Индексация завершена")

        except Exception as e:
            logger.error(f"Ошибка индексации: {e}")

    def _create_chunks(self, program_data: Dict[str, Any], program_name: str, program_id: str) -> Tuple[List[str], List[Dict]]:
        """Создает чанки из данных программы"""
        chunks = []
        metadata = []

        # Основная информация
        sections = {
            'description': program_data.get('Описание программы', ''),
            'career': program_data.get('Карьера', ''),
            'detailed_description': program_data.get('Описание (подробное)', ''),
        }

        for section_key, content in sections.items():
            if content and len(content.strip()) > 20:
                chunk = f"Программа: {program_name}\n{content}"
                chunks.append(chunk)
                metadata.append({
                    'program_name': program_name,
                    'program_id': program_id,
                    'section': section_key,
                    'type': 'content'
                })

        # FAQ
        faq = program_data.get('Вопросы и ответы', {})
        for question, answer in faq.items():
            if question and answer:
                chunk = f"Программа: {program_name}\nВопрос: {question}\nОтвет: {answer}"
                chunks.append(chunk)
                metadata.append({
                    'program_name': program_name,
                    'program_id': program_id,
                    'section': 'faq',
                    'question': question,
                    'type': 'faq'
                })

        # Техническая информация
        tech_parts = []
        if program_data.get('Стоимость для россиян'):
            tech_parts.append(f"Стоимость: {program_data['Стоимость для россиян']:,} ₽/год")
        if program_data.get('Период обучения'):
            tech_parts.append(f"Период обучения: {program_data['Период обучения']}")

        if tech_parts:
            chunk = f"Программа: {program_name}\nТехническая информация:\n" + '\n'.join(tech_parts)
            chunks.append(chunk)
            metadata.append({
                'program_name': program_name,
                'program_id': program_id,
                'section': 'technical',
                'type': 'technical'
            })

        return chunks, metadata

    def _tokenize(self, text: str) -> List[str]:
        """Токенизация текста"""
        text = text.lower()
        # Убираем знаки препинания и разбиваем
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        # Фильтруем короткие слова и стоп-слова
        stop_words = {'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о', 'об', 'что', 'как', 'это', 'тот', 'этот'}
        return [token for token in tokens if len(token) > 2 and token not in stop_words]

    def _build_tfidf_vectors(self):
        """Строит TF-IDF векторы"""
        # Токенизируем все документы
        tokenized_docs = [self._tokenize(chunk) for chunk in self.chunks]

        # Строим словарь
        all_tokens = set()
        for tokens in tokenized_docs:
            all_tokens.update(tokens)

        self.vocabulary = {token: i for i, token in enumerate(sorted(all_tokens))}

        # Вычисляем IDF
        N = len(tokenized_docs)
        doc_freq = defaultdict(int)

        for tokens in tokenized_docs:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] += 1

        self.idf_weights = {}
        for token in self.vocabulary:
            df = doc_freq.get(token, 1)
            self.idf_weights[token] = math.log(N / df)

        # Строим TF-IDF векторы
        vectors = []
        for tokens in tokenized_docs:
            vector = np.zeros(len(self.vocabulary), dtype=np.float32)
            token_counts = Counter(tokens)
            doc_length = len(tokens)

            if doc_length > 0:
                for token, count in token_counts.items():
                    if token in self.vocabulary:
                        tf = count / doc_length
                        idf = self.idf_weights[token]
                        vector[self.vocabulary[token]] = tf * idf

            # Нормализуем вектор
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            vectors.append(vector)

        self.embeddings = np.array(vectors, dtype=np.float32)
        logger.info(f"Создано {len(vectors)} TF-IDF векторов размерности {len(self.vocabulary)}")

    def _build_faiss_index(self):
        """Создает FAISS индекс"""
        if not self.faiss_available or self.embeddings is None:
            return

        try:
            import faiss

            dimension = self.embeddings.shape[1]

            # Используем IndexFlatIP для косинусной близости
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(self.embeddings)

            logger.info(f"FAISS индекс создан с {self.index.ntotal} векторами")

        except Exception as e:
            logger.error(f"Ошибка создания FAISS индекса: {e}")
            self.index = None

    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.1) -> List[Tuple[str, float, Dict]]:
        """Поиск релевантных чанков"""
        if not self.chunks:
            return []

        try:
            # Создаем вектор запроса
            query_tokens = self._tokenize(query)
            if not query_tokens:
                return []

            query_vector = np.zeros(len(self.vocabulary), dtype=np.float32)
            token_counts = Counter(query_tokens)
            doc_length = len(query_tokens)

            if doc_length > 0:
                for token, count in token_counts.items():
                    if token in self.vocabulary:
                        tf = count / doc_length
                        idf = self.idf_weights.get(token, 1.0)
                        query_vector[self.vocabulary[token]] = tf * idf

            # Нормализуем
            norm = np.linalg.norm(query_vector)
            if norm > 0:
                query_vector = query_vector / norm

            # Поиск через FAISS или numpy
            if self.index is not None:
                scores, indices = self.index.search(query_vector.reshape(1, -1), top_k)
                scores = scores[0]
                indices = indices[0]
            else:
                # Fallback к numpy косинусной близости
                similarities = np.dot(self.embeddings, query_vector)
                top_indices = np.argsort(similarities)[::-1][:top_k]
                scores = similarities[top_indices]
                indices = top_indices

            # Формируем результаты
            results = []
            for score, idx in zip(scores, indices):
                if idx != -1 and score >= score_threshold:
                    results.append((
                        self.chunks[idx],
                        float(score),
                        self.metadata[idx]
                    ))

            logger.info(f"Найдено {len(results)} результатов для '{query[:30]}...'")
            return results

        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []

    def get_program_context(self, program_name: str) -> List[Tuple[str, float, Dict]]:
        """Получает контекст программы"""
        results = []
        for i, metadata in enumerate(self.metadata):
            if metadata['program_name'] == program_name:
                results.append((
                    self.chunks[i],
                    1.0,
                    metadata
                ))
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику"""
        if not self.chunks:
            return {'status': 'not_initialized'}

        program_stats = {}
        for metadata in self.metadata:
            program = metadata['program_name']
            if program not in program_stats:
                program_stats[program] = 0
            program_stats[program] += 1

        return {
            'status': 'ready',
            'total_chunks': len(self.chunks),
            'vocabulary_size': len(self.vocabulary),
            'faiss_available': self.faiss_available,
            'model_name': 'TF-IDF + FAISS',
            'programs': program_stats
        }
