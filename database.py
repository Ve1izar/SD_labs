import sqlite3
from interfaces import IStorage


class DatabaseManager(IStorage):
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
                id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, name TEXT, detail TEXT, status TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, activity_name TEXT, completed_at TEXT
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
        cursor.execute("SELECT name FROM activities WHERE id = ?", (act_id,))
        old_name = cursor.fetchone()[0]

        cursor.execute("UPDATE activities SET name = ?, detail = ? WHERE id = ?", (new_name, detail, act_id))

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

    # Реалізація методу з IStorage
    def log_completion(self, name: str, time_str: str) -> None:
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