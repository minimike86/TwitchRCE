import json
import sqlite3


class Database:
    def __init__(self, filename='twitchrce.sqlite'):
        self.filename: str = filename
        self.conn: sqlite3.Connection | None = None
        self.open_disk()
        self.create_table()

    def open_memory(self):
        """ init memory db """
        try:
            self.conn = sqlite3.connect(':memory:')
            print("Connected to in-memory db")
        except sqlite3.Error as error:
            print("Error while connecting to memory db: ", error)

    def open_disk(self):
        """ init disk db """
        try:
            self.conn = sqlite3.connect(self.filename)
            print("Connected to disk db")
        except sqlite3.Error as error:
            print("Error while connecting to disk db: ", error)

    def create_table(self):
        """ create db table """
        cursor = self.conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, broadcaster_id INTEGER UNIQUE, broadcaster_login TEXT UNIQUE, email TEXT, access_token TEXT, expires_in INTEGER, refresh_token TEXT, scope TEXT)"
        )
        self.conn.commit()

    def insert_user_data(self, broadcaster_id, broadcaster_login, email, access_token, expires_in, refresh_token, scope):
        """ insert new record """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO users (broadcaster_id, broadcaster_login, email, access_token, expires_in, refresh_token, scope) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (int(broadcaster_id), broadcaster_login, email, access_token, int(expires_in), refresh_token, json.dumps(scope))
        )
        self.conn.commit()

    def backup_to_disk(self):
        """ backup in-memory db to disk """
        disk_conn = sqlite3.connect(self.filename)
        self.conn.backup(disk_conn)
        disk_conn.close()

    def load_from_disk(self):
        """ backup disk db to in-memory """
        disk_conn = sqlite3.connect(self.filename)
        disk_conn.backup(self.conn)
        disk_conn.close()

    def fetch_all_users(self):
        """ get all user data """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()

    def fetch_all_user_logins(self):
        """ get all user_logins data """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT broadcaster_login FROM users")
        return cursor.fetchall()

    def fetch_user_access_token_from_login(self, broadcaster_login: str):
        """ get a single users access token """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT access_token FROM users WHERE broadcaster_login = ?", (broadcaster_login,))
        return cursor.fetchone()

    def fetch_user_access_token_from_id(self, broadcaster_id: int):
        """ get a single users access token """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT access_token FROM users WHERE broadcaster_id = ?", (broadcaster_id,))
        return cursor.fetchone()

    def close(self):
        self.conn.close()
