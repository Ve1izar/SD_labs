import unittest
from unittest.mock import Mock
import sys
import os

# Додаємо кореневу папку в sys.path, щоб тести бачили наші модулі
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import ActivitySubject
from interfaces import Observer


class TestActivitySubject(unittest.TestCase):
    def setUp(self):
        # Цей метод викликається перед кожним тестом
        self.subject = ActivitySubject("Ранкова пробіжка")

    def test_initial_state(self):
        """Перевірка початкового стану нової звички"""
        self.assertEqual(self.subject.name, "Ранкова пробіжка")
        self.assertEqual(len(self.subject._observers), 0)

    def test_attach_observer(self):
        """Перевірка успішного додавання спостерігача"""
        mock_observer = Mock(spec=Observer)
        self.subject.attach(mock_observer)
        self.assertIn(mock_observer, self.subject._observers)
        self.assertEqual(len(self.subject._observers), 1)

    def test_attach_duplicate_observer(self):
        """Перевірка спроби додати того ж спостерігача двічі"""
        mock_observer = Mock(spec=Observer)
        self.subject.attach(mock_observer)
        self.subject.attach(mock_observer)  # Спроба дублювання
        self.assertEqual(len(self.subject._observers), 1, "Спостерігач не повинен дублюватися")

    def test_notify_all_observers(self):
        """Перевірка сповіщення всіх підписників"""
        mock_obs1 = Mock(spec=Observer)
        mock_obs2 = Mock(spec=Observer)

        self.subject.attach(mock_obs1)
        self.subject.attach(mock_obs2)
        self.subject.notify()

        mock_obs1.update.assert_called_once_with("Ранкова пробіжка")
        mock_obs2.update.assert_called_once_with("Ранкова пробіжка")

    def test_mark_completed_triggers_notify(self):
        """Перевірка, що виконання звички автоматично викликає сповіщення"""
        mock_observer = Mock(spec=Observer)
        self.subject.attach(mock_observer)

        self.subject.mark_completed()

        mock_observer.update.assert_called_once_with("Ранкова пробіжка")


if __name__ == '__main__':
    unittest.main()