"""
Тест упрощённой версии бота
"""
import sys
from pathlib import Path

# Добавляем корневую директорию и src в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))


def test_simple_bot():
    """Тестирует упрощённую версию бота"""
    print("🧪 Тестирование упрощённого бота...")

    try:
        from src.core.simple_chat_manager import SimpleChatManager

        # Инициализируем менеджер
        print("1. Инициализация SimpleChatManager...")
        chat_manager = SimpleChatManager()
        print("✅ SimpleChatManager инициализирован")

        # Тест 1: Обычный вопрос
        print("\n2. Тестирование обычного вопроса...")
        response = chat_manager.handle_message("test_user", "Расскажи о программе Искусственный интеллект")
        print(f"Ответ получен: {len(response)} символов")
        if len(response) > 100:
            print("✅ Развёрнутый ответ получен")
        else:
            print("⚠️ Слишком короткий ответ")

        # Тест 2: Запрос рекомендаций
        print("\n3. Тестирование запроса рекомендаций...")
        rec_response = chat_manager.handle_message(
            "test_user2",
            "Посоветуй мне программу - я программист с опытом в Python и машинном обучении"
        )
        print(f"Ответ с рекомендациями: {len(rec_response)} символов")
        if "рекомендации" in rec_response.lower() or "программа" in rec_response.lower():
            print("✅ Рекомендации получены")
        else:
            print("⚠️ Не похоже на рекомендации")

        # Тест 3: Нерелевантный вопрос
        print("\n4. Тестирование нерелевантного вопроса...")
        irrelevant_response = chat_manager.handle_message("test_user3", "Какая погода сегодня?")
        print(f"Ответ на нерелевантный вопрос: {irrelevant_response}")
        if "отвечаю только" in irrelevant_response.lower():
            print("✅ Нерелевантный вопрос отфильтрован")
        else:
            print("⚠️ Фильтрация не сработала")

        print("\n🎉 Тестирование упрощённого бота завершено!")

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_simple_bot()
