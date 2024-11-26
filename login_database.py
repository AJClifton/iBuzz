import sqlite3
import os
import threading
import werkzeug.security
import uuid
from user import User


def hash_password(password):
    return werkzeug.security.generate_password_hash(password, 'pbkdf2:sha256')


def verify_password(user, password):
    return werkzeug.security.check_password_hash(user.password, password)


class LoginDatabase:
    database_path = "logins.db"
    database_lock = threading.Lock()

    def __init__(self):
        database_exists = os.path.isfile(self.database_path)
        self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
        if not database_exists:
            self.connection.execute("""CREATE TABLE Logins (
                                    Id	TEXT,
                                    First_name TEXT,
                                    Email	TEXT,
                                    Password	TEXT,
                                    PRIMARY KEY(Id)
                                );""")

    def fetch_user(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM Logins WHERE Id = (?)""", (user_id, ))
        item = cursor.fetchone()
        return None if item is None else User(*item)

    def fetch_user_by_email(self, email):
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM Logins WHERE Email = (?)""", (email, ))
        item = cursor.fetchone()
        return None if item is None else User(*item)

    def add_user(self, first_name, email, password):
        hashed_password = hash_password(password)
        user_id = str(uuid.uuid4())
        while not self.check_unique_user_id(user_id):
            user_id = str(uuid.uuid4())
        self.database_lock.acquire()
        self.connection.execute("""INSERT INTO Logins VALUES (?, ?, ?, ?)""", (user_id, first_name, email, hashed_password))
        self.connection.commit()
        self.database_lock.release()

    def check_unique_user_id(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM Logins WHERE Id = (?)""", (user_id,))
        item = cursor.fetchone()
        return item is None

