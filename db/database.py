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
        cursor.execute("CREATE TABLE IF NOT EXISTS app (id INTEGER PRIMARY KEY, access_token TEXT, expires_in INTEGER, token_type TEXT UNIQUE)")
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, broadcaster_id INTEGER UNIQUE, broadcaster_login TEXT UNIQUE, email TEXT, access_token TEXT, expires_in INTEGER, refresh_token TEXT, scope TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS sub (id INTEGER PRIMARY KEY, broadcaster_id INTEGER, broadcaster_login TEXT, broadcaster_name TEXT, gifter_id INTEGER, gifter_login TEXT, gifter_name TEXT, is_gift INTEGER, plan_name TEXT, tier INTEGER, user_id INTEGER UNIQUE, user_name TEXT, user_login TEXT UNIQUE, is_active INTEGER, timestamp INTEGER)")
        cursor.execute("CREATE TABLE IF NOT EXISTS raid (id INTEGER PRIMARY KEY, raider_id INTEGER, raider_login TEXT, receiver_id INTEGER, receiver_login TEXT, viewer_count INTEGER, timestamp INTEGER )")
        self.conn.commit()

    def insert_app_data(self, access_token, expires_in, token_type):
        """ insert new app record """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO app (access_token, expires_in, token_type) VALUES (?, ?, ?)",
            (access_token, int(expires_in), token_type)
        )
        self.conn.commit()

    def insert_user_data(self, broadcaster_id, broadcaster_login, email, access_token, expires_in, refresh_token, scope):
        """ insert new user record """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO users (broadcaster_id, broadcaster_login, email, access_token, expires_in, refresh_token, scope) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (int(broadcaster_id), broadcaster_login, email, access_token, int(expires_in), refresh_token, json.dumps(scope))
        )
        self.conn.commit()

    def update_all_subs_inactive(self):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE sub SET is_active = 0")
        self.conn.commit()

    def insert_sub_data(self, broadcaster_id: str, broadcaster_login: str, broadcaster_name: str,
                        gifter_id: str, gifter_login: str, gifter_name: str, is_gift: bool,
                        plan_name: str, tier: str, user_id: str, user_name: str, user_login: str, is_active: bool):
        """ insert new sub record """
        gifter_id = None if gifter_id == '' else gifter_id
        gifter_login = None if gifter_login == '' else gifter_login
        gifter_name = None if gifter_name == '' else gifter_name
        is_gift = 1 if is_gift else 0
        is_active = 1 if is_active else 0
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO sub (broadcaster_id, broadcaster_login, broadcaster_name, gifter_id, gifter_login, gifter_name, is_gift, plan_name, tier, user_id, user_name, user_login, is_active, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, unixepoch())",
            (int(broadcaster_id), broadcaster_login, broadcaster_name,
             gifter_id, gifter_login, gifter_name, is_gift,
             plan_name, tier, int(user_id), user_name, user_login, is_active)
        )
        self.conn.commit()

    def insert_raid_data(self, raider_id, raider_login, receiver_id, receiver_login, viewer_count):
        """ insert new raid record """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO raid (raider_id, raider_login, receiver_id, receiver_login, viewer_count, timestamp) VALUES (?, ?, ?, ?, ?, unixepoch())",
            (int(raider_id), raider_login, int(receiver_id), receiver_login, int(viewer_count))
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

    def fetch_app_token(self):
        """ get all user data """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM app")
        return cursor.fetchall()

    def fetch_user_from_id(self, broadcaster_id: str):
        """ get all user data """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE broadcaster_id = ?", (broadcaster_id,))
        return cursor.fetchall()

    def fetch_user_from_login(self, broadcaster_login: str):
        """ get all user data """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE broadcaster_login = ?", (broadcaster_login,))
        return cursor.fetchall()

    def fetch_all_users(self):
        """ get all user data """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()

    def fetch_user_access_token_from_id(self, broadcaster_id: int):
        """ get a single users access token """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT access_token FROM users WHERE broadcaster_id = ?", (broadcaster_id,))
        return cursor.fetchone()

    def fetch_user_access_token_from_login(self, broadcaster_login: str):
        """ get a single users access token """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT access_token FROM users WHERE broadcaster_login = ?", (broadcaster_login,))
        return cursor.fetchone()

    def fetch_all_user_logins(self):
        """ get all user_logins data """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT broadcaster_login FROM users")
        return cursor.fetchall()

    def fetch_raids_from_id(self, raider_id: int):
        """ get a single users access token """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM raid WHERE raider_id = ?", (raider_id,))
        return cursor.fetchall()

    def fetch_raids_from_login(self, raider_login: str):
        """ get a single users access token """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM raid WHERE raider_login = ?", (raider_login,))
        return cursor.fetchall()

    def close(self):
        self.conn.close()
