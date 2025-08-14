"""
Менеджер контекста пользователей
"""
import sqlite3
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

from src.core.config import Config

logger = logging.getLogger(__name__)


class ContextManager:
    """Управляет контекстом и историей диалогов пользователей"""

    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self._init_database()
        logger.info("ContextManager инициализирован")

    def _init_database(self):
        """Инициализирует базу данных"""
        # Создаем директорию если не существует
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    background TEXT,
                    interests TEXT,  -- JSON массив
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица истории сообщений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    question TEXT,
                    answer TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            conn.commit()

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Получает контекст пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Получаем информацию о пользователе
                cursor.execute(
                    'SELECT background, interests FROM users WHERE user_id = ?',
                    (user_id,)
                )
                user_data = cursor.fetchone()

                # Получаем историю сообщений (последние 10)
                cursor.execute('''
                    SELECT question, answer, timestamp 
                    FROM messages 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                ''', (user_id,))

                history = [
                    {
                        'question': row[0],
                        'answer': row[1],
                        'timestamp': row[2]
                    }
                    for row in cursor.fetchall()
                ]

                context = {
                    'user_id': user_id,
                    'background': user_data[0] if user_data else '',
                    'interests': json.loads(user_data[1]) if user_data and user_data[1] else [],
                    'history': list(reversed(history))  # Сортируем по возрастанию времени
                }

                return context

        except Exception as e:
            logger.error(f"Ошибка получения контекста пользователя {user_id}: {e}")
            return {
                'user_id': user_id,
                'background': '',
                'interests': [],
                'history': []
            }

    def update_user_info(self, user_id: str, background: str, interests: List[str]):
        """Обновляет информацию о пользователе"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                interests_json = json.dumps(interests, ensure_ascii=False)

                cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, background, interests, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, background, interests_json, datetime.now()))

                conn.commit()
                logger.info(f"Обновлена информация пользователя {user_id}")

        except Exception as e:
            logger.error(f"Ошибка обновления информации пользователя {user_id}: {e}")

    def add_message(self, user_id: str, question: str, answer: str):
        """Добавляет сообщение в историю"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO messages (user_id, question, answer)
                    VALUES (?, ?, ?)
                ''', (user_id, question, answer))

                conn.commit()

                # Ограничиваем историю (оставляем последние 50 сообщений)
                cursor.execute('''
                    DELETE FROM messages 
                    WHERE user_id = ? AND id NOT IN (
                        SELECT id FROM messages 
                        WHERE user_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 50
                    )
                ''', (user_id, user_id))

                conn.commit()

        except Exception as e:
            logger.error(f"Ошибка добавления сообщения для пользователя {user_id}: {e}")

    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Получает историю сообщений пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT question, answer, timestamp 
                    FROM messages 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (user_id, limit))

                history = [
                    {
                        'question': row[0],
                        'answer': row[1],
                        'timestamp': row[2]
                    }
                    for row in cursor.fetchall()
                ]

                return list(reversed(history))

        except Exception as e:
            logger.error(f"Ошибка получения истории пользователя {user_id}: {e}")
            return []

    def clear_user_history(self, user_id: str):
        """Очищает историю пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('DELETE FROM messages WHERE user_id = ?', (user_id,))
                conn.commit()

                logger.info(f"История пользователя {user_id} очищена")

        except Exception as e:
            logger.error(f"Ошибка очистки истории пользователя {user_id}: {e}")

    def get_user_stats(self) -> Dict[str, Any]:
        """Получает статистику по пользователям"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Общее количество пользователей
                cursor.execute('SELECT COUNT(*) FROM users')
                total_users = cursor.fetchone()[0]

                # Количество сообщений
                cursor.execute('SELECT COUNT(*) FROM messages')
                total_messages = cursor.fetchone()[0]

                # Активные пользователи (сообщения за последние 7 дней)
                cursor.execute('''
                    SELECT COUNT(DISTINCT user_id) FROM messages 
                    WHERE timestamp > datetime('now', '-7 days')
                ''')
                active_users = cursor.fetchone()[0]

                return {
                    'total_users': total_users,
                    'total_messages': total_messages,
                    'active_users_week': active_users
                }

        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {'total_users': 0, 'total_messages': 0, 'active_users_week': 0}
