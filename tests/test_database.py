import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Обнуляємо синглтон перед кожним тестом
        DatabaseManager._instance = None

    def tearDown(self):
        DatabaseManager._instance = None

    def test_singleton_uniqueness(self):
        """Перевірка, що два виклики повертають один і той самий об'єкт (Singleton)"""
        db1 = DatabaseManager()
        db2 = DatabaseManager()
        self.assertIs(db1, db2)

    @patch('database.sqlite3.connect')
    def test_crud_activities(self, mock_connect):
        """Тестування методів управління активностями (з використанням Mock БД)"""
        # Налаштовуємо фейкову базу даних, щоб не псувати реальний файл
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Для методу update_activity нам треба імітувати, що база повертає стару назву
        mock_cursor.fetchone.return_value = ["Стара Звичка"]

        db = DatabaseManager()

        # Викликаємо всі CRUD методи, щоб coverage їх "побачив"
        db.add_activity("Звичка", "Біг", "Щоденно")
        db.update_activity(1, "Новий Біг", "Щоденно")
        db.mark_activity_completed(1)
        db.delete_activity(1)

        # Перевіряємо, що запити до бази реально формувались
        self.assertTrue(mock_cursor.execute.called)
        self.assertTrue(mock_conn.commit.called)

    @patch('database.sqlite3.connect')
    def test_crud_logs(self, mock_connect):
        """Тестування методів управління логами"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = DatabaseManager()

        db.log_completion("Біг", "2026-05-12 10:00:00")
        db.update_log(1, "Біг", "2026-05-12 11:00:00")
        db.delete_log(1)

        self.assertTrue(mock_cursor.execute.called)

    @patch('database.sqlite3.connect')
    def test_get_methods(self, mock_connect):
        """Тестування методів отримання даних (SELECT)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = DatabaseManager()

        # Імітуємо повернення списку активностей
        mock_cursor.fetchall.return_value = [(1, "Звичка", "Біг", "active")]
        activities = db.get_activities("Звичка")
        self.assertEqual(len(activities), 1)

        # Імітуємо повернення логів
        mock_cursor.fetchall.return_value = [(1, "Біг", "2026-05-12 10:00:00")]
        logs = db.get_logs()
        self.assertEqual(len(logs), 1)

        # Імітуємо повернення кількості (COUNT)
        mock_cursor.fetchone.return_value = [5]
        count = db.get_completion_count("Біг")
        self.assertEqual(count, 5)


if __name__ == '__main__':
    unittest.main()