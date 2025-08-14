"""
Конфигурация чат-бота ИТМО
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    """Основная конфигурация приложения"""

    # Пути к данным
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    JSON_DATA_PATH = DATA_DIR
    PDF_DATA_PATH = DATA_DIR / "downloaded_pdfs"
    DATABASE_PATH = DATA_DIR / "chat_context.db"

    # API ключи
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # Настройки LLM
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

    # Программы ИТМО
    PROGRAMS = {
        "ai": "Искусственный интеллект",
        "ai_product": "Управление ИИ-продуктами"
    }

    # Валидация обязательных настроек
    @classmethod
    def validate(cls):
        """Проверяет наличие обязательных настроек"""
        missing = []

        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")

        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")

        if missing:
            raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}")

        return True
