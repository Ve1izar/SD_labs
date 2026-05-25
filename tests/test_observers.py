import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from observers import DBLogObserver, StreamlitNotifier
from interfaces import IStorage


class TestObservers(unittest.TestCase):
    def setUp(self):
        # Створюємо заглушку для бази даних
        self.mock_storage = Mock(spec=IStorage)
        # Використовуємо Dependency Injection
        self.db_observer = DBLogObserver(storage=self.mock_storage)

    @patch('observers.datetime')
    def test_db_observer_calls_storage(self, mock_datetime):
        """Перевірка, що DBLogObserver викликає метод бази даних з правильним часом"""
        # Налаштовуємо фейковий час
        mock_datetime.now.return_value.strftime.return_value = '2026-05-15 10:00:00'

        self.db_observer.update("Медитація")

        # Перевіряємо, що заглушка БД отримала правильні дані
        self.mock_storage.log_completion.assert_called_once_with("Медитація", '2026-05-15 10:00:00')

    @patch('observers.datetime')
    def test_db_observer_multiple_updates(self, mock_datetime):
        """Перевірка, що спостерігач коректно обробляє кілька подій підряд"""
        mock_datetime.now.return_value.strftime.return_value = '2026-05-15 10:05:00'

        self.db_observer.update("Біг")
        self.db_observer.update("Читання")

        self.assertEqual(self.mock_storage.log_completion.call_count, 2)

    @patch('observers.st')
    def test_streamlit_notifier_success(self, mock_st):
        """Перевірка UI сповіщення: запис повідомлення в session_state"""
        ui_observer = StreamlitNotifier()
        ui_observer.update("Вивчення Python")

        # Перевіряємо, що у фейковий Streamlit записалась правильна змінна
        self.assertEqual(mock_st.session_state.show_success, "Вивчення Python")


if __name__ == '__main__':
    unittest.main()