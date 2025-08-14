"""
Главный файл для запуска ИТМО чат-бота
"""
from src.core.config import Config
from src.bot.bot import ITMOChatBot
import sys
import logging
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.append(str(Path(__file__).parent / "src"))


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Главная функция запуска бота"""
    try:
        print("🎓 Инициализация ИТМО чат-бота...")

        # Проверяем конфигурацию
        Config.validate()
        print("✅ Конфигурация проверена")

        # Создаем и запускаем бота
        bot = ITMOChatBot()
        print("✅ Бот инициализирован")

        # Запускаем
        bot.run()

    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        print("\n📝 Инструкции:")
        print("1. Скопируйте config_example.env в .env")
        print("2. Заполните OPENAI_API_KEY и TELEGRAM_BOT_TOKEN")
        print("3. Запустите бота снова")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
