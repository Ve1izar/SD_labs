from abc import ABC, abstractmethod

# Інтерфейс 1: Для реалізації патерну Observer
class Observer(ABC):
    @abstractmethod
    def update(self, activity_name: str) -> None:
        pass

# Інтерфейс 2: Для абстрагування роботи з базою даних (DIP)
class IStorage(ABC):
    @abstractmethod
    def log_completion(self, name: str, time_str: str) -> None:
        """Метод для збереження запису про виконання"""
        pass