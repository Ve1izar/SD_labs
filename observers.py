import streamlit as st
from datetime import datetime
from interfaces import Observer, IStorage

class StreamlitNotifier(Observer):
    def update(self, activity_name: str) -> None:
        st.session_state.show_success = activity_name

class DBLogObserver(Observer):
    # Отримуємо будь-яке сховище, яке відповідає інтерфейсу IStorage
    def __init__(self, storage: IStorage):
        self.storage = storage

    def update(self, activity_name: str) -> None:
        time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Викликаємо метод інтерфейсу, а не напряму DatabaseManager
        self.storage.log_completion(activity_name, time_now)