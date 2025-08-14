"""
Тест пользовательского интерфейса бота (без административных команд)
"""
import sys
from pathlib import Path

# Добавляем корневую директорию и src в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))


def test_user_interface():
    """Тестирует пользовательский интерфейс"""
    print("🧪 Тестирование пользовательского интерфейса...")

    try:
        from src.core.chat_manager import ChatManager

        # Инициализируем менеджер
        print("1. Инициализация ChatManager...")
        chat_manager = ChatManager()
        print("✅ ChatManager инициализирован")

        # Тест 1: Информационный запрос
        print("\n2. Тестирование информационных запросов...")
        test_queries = [
            "Расскажи о программе Искусственный интеллект",
            "Сколько стоит обучение?",
            "Какие требования для поступления?",
            "Чем отличаются программы?",
        ]

        for query in test_queries:
            print(f"Запрос: '{query}'")
            response = chat_manager.handle_message("test_user_1", query)
            print(f"Ответ получен: {len(response)} символов")
            # Проверяем, что ответ не является сообщением о нерелевантности
            if "специализируюсь только на вопросах" not in response:
                print("✅ Релевантный ответ")
            else:
                print("⚠️ Нерелевантный ответ")

        # Тест 2: Сохранение бэкграунда
        print("\n3. Тестирование сохранения бэкграунда...")
        background = "Я backend-разработчик на Python с опытом 3 года. Работал с Django и PostgreSQL. Интересуюсь машинным обучением и хочу развиваться в сторону ML-инженера."

        response = chat_manager.set_user_background("test_user_2", background)
        print("✅ Бэкграунд сохранен")

        # Тест 3: Запрос рекомендаций
        print("\n4. Тестирование запроса рекомендаций...")
        recommendation_queries = [
            "Посоветуй мне дисциплины",
            "Какую программу выбрать?",
            "Рекомендации по обучению",
            "Что изучать?",
        ]

        for query in recommendation_queries:
            print(f"Запрос рекомендации: '{query}'")
            response = chat_manager.handle_message("test_user_2", query)

            if "Персональные рекомендации" in response or "рекомендации" in response.lower():
                print("✅ Рекомендации сгенерированы")
            elif "специализируюсь только на вопросах" in response:
                print("⚠️ Классификатор не распознал запрос рекомендаций")
            else:
                print("✅ Получен ответ")

        # Тест 4: Контекстность диалога
        print("\n5. Тестирование контекстности диалога...")
        user_id = "test_user_3"

        # Задаем контекст
        chat_manager.handle_message(user_id, "Расскажи о программе Искусственный интеллект")

        # Задаем уточняющий вопрос
        response = chat_manager.handle_message(user_id, "А сколько это стоит?")
        print(f"Контекстный ответ получен: {len(response)} символов")

        if "стоимость" in response.lower() or "₽" in response:
            print("✅ Контекст учтен")
        else:
            print("⚠️ Контекст не учтен")

        # Тест 5: Проверка фильтрации нерелевантных вопросов
        print("\n6. Тестирование фильтрации нерелевантных вопросов...")
        irrelevant_queries = [
            "Какая погода сегодня?",
            "Как приготовить борщ?",
            "Расскажи анекдот",
        ]

        for query in irrelevant_queries:
            response = chat_manager.handle_message("test_user_4", query)
            if "специализируюсь только на вопросах" in response:
                print(f"✅ Нерелевантный вопрос отфильтрован: '{query}'")
            else:
                print(f"⚠️ Нерелевантный вопрос пропущен: '{query}'")

        print("\n🎉 Тестирование пользовательского интерфейса завершено!")

        # Краткая статистика RAG
        try:
            rag_stats = chat_manager.data_loader.get_rag_stats()
            print(f"\n📊 RAG статистика: {rag_stats['status']}")
            if rag_stats['status'] == 'ready':
                print(f"Всего чанков: {rag_stats.get('total_chunks', 0)}")

        except Exception as e:
            print(f"Статистика RAG недоступна: {e}")

        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_user_interface()
