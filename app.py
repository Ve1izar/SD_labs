import streamlit as st
import sqlite3
import re
from datetime import datetime, date
from abc import ABC, abstractmethod


# ==========================================
# 1. Singleton: Локальна База Даних (CRUD)
# ==========================================
class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.conn = sqlite3.connect("local_tracker.db", check_same_thread=False)
            cls._instance.create_tables()
        return cls._instance

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT, 
                name TEXT,
                detail TEXT, 
                status TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_name TEXT,
                completed_at TEXT
            )
        """)
        self.conn.commit()

    def add_activity(self, act_type: str, name: str, detail: str):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO activities (type, name, detail, status) VALUES (?, ?, ?, 'active')",
                       (act_type, name, detail))
        self.conn.commit()

    def get_activities(self, act_type: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, detail, status FROM activities WHERE type = ? AND status = 'active'",
                       (act_type,))
        return cursor.fetchall()

    def update_activity(self, act_id: int, new_name: str, detail: str):
        cursor = self.conn.cursor()
        # Спочатку дізнаємося стару назву, щоб оновити її і в логах (щоб не втратити історію)
        cursor.execute("SELECT name FROM activities WHERE id = ?", (act_id,))
        old_name = cursor.fetchone()[0]

        cursor.execute("UPDATE activities SET name = ?, detail = ? WHERE id = ?", (new_name, detail, act_id))

        # Якщо назва змінилась, оновлюємо її в логах, щоб статистика не розірвалась
        if old_name != new_name:
            cursor.execute("UPDATE logs SET activity_name = ? WHERE activity_name = ?", (new_name, old_name))

        self.conn.commit()

    def delete_activity(self, act_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM activities WHERE id = ?", (act_id,))
        self.conn.commit()

    def mark_activity_completed(self, act_id: int):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE activities SET status = 'completed' WHERE id = ?", (act_id,))
        self.conn.commit()

    # --- Методи для логів ---
    def log_completion(self, name: str, time_str: str):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO logs (activity_name, completed_at) VALUES (?, ?)", (name, time_str))
        self.conn.commit()

    def get_logs(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, activity_name, completed_at FROM logs ORDER BY id DESC")
        return cursor.fetchall()

    def get_completion_count(self, name: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs WHERE activity_name = ?", (name,))
        return cursor.fetchone()[0]

    def update_log(self, log_id: int, new_name: str, new_time: str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE logs SET activity_name = ?, completed_at = ? WHERE id = ?", (new_name, new_time, log_id))
        self.conn.commit()

    def delete_log(self, log_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM logs WHERE id = ?", (log_id,))
        self.conn.commit()


# ==========================================
# 2. Observer: Система подій
# ==========================================
class Observer(ABC):
    @abstractmethod
    def update(self, activity_name: str):
        pass


class ActivitySubject:
    def __init__(self, name: str):
        self.name = name
        self._observers = []

    def attach(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def notify(self):
        for obs in self._observers:
            obs.update(self.name)

    def mark_completed(self):
        self.notify()


class StreamlitNotifier(Observer):
    def update(self, activity_name: str):
        st.session_state.show_success = activity_name


class DBLogObserver(Observer):
    def update(self, activity_name: str):
        time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db = DatabaseManager()
        db.log_completion(activity_name, time_now)


# ==========================================
# 3. Інтерфейс Streamlit
# ==========================================
def render_crud_interface(page_type: str, detail_label: str):
    db = DatabaseManager()

    st.header(f"Управління: {page_type.capitalize()}")

    with st.expander(f"➕ Додати нове {page_type.lower()}", expanded=True):
        new_name = st.text_input("Назва", key=f"new_name_{page_type}")

        if page_type == "Завдання":
            new_detail_raw = st.date_input("Дедлайн", key=f"new_dead_{page_type}")
        else:
            freq_type = st.selectbox("Частота", ["Щоденно", "Щотижнево", "Щомісячно"], key=f"freq_type_{page_type}")

            if freq_type == "Щотижнево":
                day_of_week = st.selectbox("Оберіть день тижня",
                                           ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота",
                                            "Неділя"], key=f"dow_{page_type}")
                new_detail_raw = f"Щотижнево ({day_of_week})"
            elif freq_type == "Щомісячно":
                monthly_date = st.date_input("Оберіть дату в календарі (система запам'ятає число)",
                                             key=f"dom_{page_type}")
                new_detail_raw = f"Щомісячно ({monthly_date.day}-го числа)"
            else:
                new_detail_raw = "Щоденно"

        if st.button("Зберегти", key=f"save_btn_{page_type}"):
            if new_name:
                if page_type == "Завдання":
                    new_detail = new_detail_raw.strftime('%d.%m.%Y')
                else:
                    new_detail = new_detail_raw

                db.add_activity(page_type, new_name, new_detail)
                st.success("Додано успішно!")
                st.rerun()
            else:
                st.error("Назва не може бути порожньою.")

    st.divider()

    activities = db.get_activities(page_type)

    if not activities:
        st.info(f"Список порожній або всі елементи виконані. Додайте нове {page_type.lower()}!")
        return

    for act in activities:
        act_id, name, detail, status = act

        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.subheader(name)
                st.write(f"*{detail_label}:* {detail}")

                # Показуємо кількість виконань для Звичок
                if page_type == "Звичка":
                    count = db.get_completion_count(name)
                    st.write(f"🔥 Виконано: **{count}** разів")

            with col2:
                if st.button("✅ Виконати", key=f"complete_{act_id}"):
                    # ЗАВДАННЯ ЗНИКАЄ. ЗВИЧКА ЗАЛИШАЄТЬСЯ.
                    if page_type == "Завдання":
                        db.mark_activity_completed(act_id)

                    subject = ActivitySubject(name)
                    subject.attach(StreamlitNotifier())
                    subject.attach(DBLogObserver())
                    subject.mark_completed()
                    st.rerun()

            with col3:
                with st.popover("✏️ Редагувати"):
                    edit_name = st.text_input("Нова назва", value=name, key=f"edit_name_{act_id}")

                    if page_type == "Завдання":
                        try:
                            current_date = datetime.strptime(detail, '%d.%m.%Y').date()
                        except ValueError:
                            current_date = datetime.now().date()
                        edit_detail_raw = st.date_input("Новий дедлайн", value=current_date, key=f"edit_det_{act_id}")

                    else:
                        default_idx = 0
                        default_dow_idx = 0
                        default_dom_date = datetime.now().date()

                        if "Щотижнево" in detail:
                            default_idx = 1
                            days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]
                            for i, d in enumerate(days):
                                if d in detail:
                                    default_dow_idx = i
                                    break
                        elif "Щомісячно" in detail:
                            default_idx = 2
                            match = re.search(r'\d+', detail)
                            if match:
                                day = int(match.group())
                                try:
                                    default_dom_date = datetime.now().date().replace(day=day)
                                except ValueError:
                                    default_dom_date = date(datetime.now().year, 1, day)

                        edit_freq = st.selectbox("Частота", ["Щоденно", "Щотижнево", "Щомісячно"], index=default_idx,
                                                 key=f"freq_{act_id}")

                        if edit_freq == "Щотижнево":
                            edit_dow = st.selectbox("День тижня",
                                                    ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота",
                                                     "Неділя"], index=default_dow_idx, key=f"dow_{act_id}")
                            edit_detail_raw = f"Щотижнево ({edit_dow})"
                        elif edit_freq == "Щомісячно":
                            edit_monthly_date = st.date_input("Оберіть дату в календарі", value=default_dom_date,
                                                              key=f"dom_{act_id}")
                            edit_detail_raw = f"Щомісячно ({edit_monthly_date.day}-го числа)"
                        else:
                            edit_detail_raw = "Щоденно"

                    if st.button("Зберегти зміни", key=f"save_{act_id}"):
                        if page_type == "Завдання":
                            edit_detail = edit_detail_raw.strftime('%d.%m.%Y')
                        else:
                            edit_detail = edit_detail_raw

                        db.update_activity(act_id, edit_name, edit_detail)
                        st.rerun()

                if st.button("🗑️ Видалити", key=f"del_{act_id}"):
                    db.delete_activity(act_id)
                    st.rerun()


def main():
    st.set_page_config(page_title="Task & Habit Tracker", page_icon="📝")
    st.title("Локальний Трекер")

    if 'show_success' in st.session_state:
        st.success(f"🎉 Виконано: '{st.session_state.show_success}'!")
        st.balloons()
        del st.session_state.show_success

    menu = st.sidebar.radio("Навігація", ["📋 Завдання", "🔁 Звички", "📊 Статистика (Логи)"])

    if menu == "📋 Завдання":
        render_crud_interface(page_type="Завдання", detail_label="Дедлайн")

    elif menu == "🔁 Звички":
        render_crud_interface(page_type="Звичка", detail_label="Частота")

    elif menu == "📊 Статистика (Логи)":
        st.header("Історія виконання")
        db = DatabaseManager()
        logs = db.get_logs()

        if not logs:
            st.info("Історія порожня. Виконайте будь-яку звичку або завдання!")
        else:
            # 1. Загальна статистика
            st.subheader("📊 Кількість повторень")
            stats = {}
            for log in logs:
                name = log[1]
                stats[name] = stats.get(name, 0) + 1

            for name, count in stats.items():
                st.write(f"- **{name}**: {count} разів")

            st.divider()

            # 2. Детальні записи з можливістю CRUD
            st.subheader("📝 Редагування записів")
            for log in logs:
                log_id, name, completed_at = log

                with st.container(border=True):
                    col_l1, col_l2, col_l3 = st.columns([3, 1, 1])

                    with col_l1:
                        st.write(f"✅ **{name}** — *{completed_at}*")

                    with col_l2:
                        with st.popover("✏️"):
                            new_log_name = st.text_input("Назва", value=name, key=f"log_name_{log_id}")
                            new_log_time = st.text_input("Час", value=completed_at, key=f"log_time_{log_id}")
                            if st.button("Зберегти", key=f"log_save_{log_id}"):
                                db.update_log(log_id, new_log_name, new_log_time)
                                st.rerun()

                    with col_l3:
                        if st.button("🗑️", key=f"log_del_{log_id}"):
                            db.delete_log(log_id)
                            st.rerun()


if __name__ == "__main__":
    main()