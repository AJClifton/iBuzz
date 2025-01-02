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

    database_lock = threading.Lock()

    def __init__(self, database_path="logins.db"):
        self.database_path = database_path
        database_exists = os.path.isfile(self.database_path)
        self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
        if not database_exists:
            self.connection.execute("""CREATE TABLE Logins (
                                    user_id	TEXT,
                                    first_name TEXT,
                                    email	TEXT,
                                    password	TEXT,
                                    PRIMARY KEY(user_id)
                                );""")
            self.connection.execute("""CREATE TABLE HawkOwnership (
                                    user_id	TEXT,
                                    serial_number INTEGER,
                                    PRIMARY KEY(serial_number)
                                );""")
            self.connection.execute("""CREATE TABLE HawkVisibility (
                                    user_id	TEXT,
                                    serial_number INTEGER,
                                    PRIMARY KEY(user_id, serial_number)
                                );""")
            self.connection.execute("""CREATE TABLE Notifications (
                                    notification_id TEXT,
                                    user_id TEXT,
                                    serial_number INTEGER,
                                    hive_number INTEGER,
                                    sensor TEXT,
                                    sign TEXT,
                                    value NUMERIC,
                                    PRIMARY KEY(notification_id)
                                );""")

    def close(self):
        """Close database connection."""
        self.connection.close()

    def fetch_user(self, user_id):
        """Return a user object for a given user_id.

        :param str user_id: uuid4
        :returns: User object if user_id exists, otherwise None"""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM Logins WHERE user_id = (?)""", (user_id,))
        item = cursor.fetchone()
        return None if item is None else User(*item)

    def fetch_user_by_email(self, email):
        """Return a user object for a given email.

        :returns: User object if email exists in database, otherwise None"""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM Logins WHERE email = (?)""", (email,))
        item = cursor.fetchone()
        return None if item is None else User(*item)

    def add_user(self, first_name, email, password):
        """Add a user to the database.

        Adds first_name, email, and hashed password to database along with a generated unique user_id.
        :type first_name: str
        :type email: str
        :type password: str"""
        hashed_password = hash_password(password)
        user_id = str(uuid.uuid4())
        while not self.check_unique_user_id(user_id):
            user_id = str(uuid.uuid4())
        with self.connection:
            self.connection.execute(
                """INSERT INTO Logins VALUES (?, ?, ?, ?)""",
                (user_id, first_name, email, hashed_password))

    def check_unique_user_id(self, user_id):
        """Return False if the uuid exists in the database, True otherwise."""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM Logins WHERE user_id = (?)""", (user_id,))
        item = cursor.fetchone()
        return item is None

    def register_hawk(self, user_id, serial_number):
        """Add ownership of a hawk to a user account.

        :type user_id: str
        :param int serial_number: Serial Number assigned by Digital Matter to the Hawk
        :raises sqlite3.IntegrityError: if the serial_number is already assigned to a user_id
        :raises ValueError: if serial_number isn't an integer"""
        serial_number = int(serial_number)
        with self.connection:
            self.connection.execute(
                """INSERT INTO HawkOwnership VALUES (?, ?)""", (user_id, serial_number))

    def deregister_hawk(self, user_id, serial_number):
        """Remove a hawk from a user account.

        Removes ownership of a hawk from a user_id and removes all visibility permissions.
        :type user_id: str
        :param int serial_number: Serial Number assigned by Digital Matter to the Hawk
        :raises PermissionError: if user_id doesn't own the Hawk serial_number
        :raises ValueError: if serial_number isn't an integer"""
        if not self.check_hawk_ownership(user_id, serial_number):
            raise PermissionError
        with self.connection:
            self.connection.execute(
                """DELETE FROM HawkOwnership WHERE user_id = (?) and serial_number = (?)""", (user_id, serial_number))
        self.remove_all_hawk_visibility(user_id, serial_number)

    def check_hawk_ownership(self, user_id, serial_number):
        """Check if user_id owns the Hawk with the given serial_number.

        :type user_id: str
        :type serial_number: int"""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM HawkOwnership WHERE user_id = (?) and serial_number = (?)""", (user_id, serial_number))
        item = cursor.fetchone()
        return item is not None

    def add_hawk_visibility(self, owner_user_id, serial_number, target_user_id):
        """Give visibility permissions for a hawk's data to a user_id.

        Using 'ALL' as a user_id will give universal visibility permissions.
        :param str owner_user_id: uuid of the user that owns the Hawk
        :param int serial_number: Serial Number assigned by Digital Matter to the Hawk
        :param str target_user_id: uuid or 'ALL' that will be given viewing permissions
        :raises PermissionError: if granting_user_id doesn't own the Hawk serial_number
        :raises ValueError: if target_user_id doesn't exist"""
        if not self.check_hawk_ownership(owner_user_id, serial_number):
            raise PermissionError
        if target_user_id != 'ALL':
            if self.fetch_user(target_user_id) is None:
                raise ValueError
        try:
            with self.connection:
                self.connection.execute(
                    """INSERT INTO HawkVisibility VALUES (?, ?)""", (target_user_id, serial_number))
        # There is no need for an error if the permission has already been given before.
        except sqlite3.IntegrityError as e:
            pass

    def remove_hawk_visibility(self, owner_user_id, serial_number, target_user_id):
        """Remove visibility permissions for a hawk's data from a user_id.

        Using 'ALL' as a user_id will remove universal permissions but NOT remove individually given permissions
        :param str owner_user_id: uuid of the user that owns the Hawk
        :param int serial_number: Serial Number assigned by Digital Matter to the Hawk
        :param str target_user_id: uuid or 'ALL' that will lose viewing permissions
        :raises PermissionError: if granting_user_id doesn't own the Hawk serial_number"""
        if not self.check_hawk_ownership(owner_user_id, serial_number):
            raise PermissionError
        with self.connection:
            self.connection.execute(
                """DELETE FROM HawkVisibility WHERE user_id = (?) and serial_number = (?)""", (target_user_id, serial_number))

    def remove_all_hawk_visibility(self, owner_user_id, serial_number):
        """Remove all visibility permissions for a hawk.

        :param str owner_user_id: uuid of the user that owns the Hawk
        :param int serial_number: Serial Number assigned by Digital Matter to the Hawk
        :raises PermissionError: if granting_user_id doesn't own the Hawk serial_number"""
        if not self.check_hawk_ownership(owner_user_id, serial_number):
            raise PermissionError
        with self.connection:
            self.connection.execute(
                """DELETE FROM HawkVisibility WHERE serial_number = (?)""", (serial_number,))

    def check_visibility_permissions(self, user_id, serial_number):
        """Check if the given user_id has permission to view the Hawk with the given serial_number."""
        if self.check_hawk_ownership(user_id, serial_number):
            return True
        cursor = self.connection.cursor()
        cursor.execute(
            """SELECT * FROM HawkVisibility WHERE user_id = (?) and (serial_number = (?) or serial_number = (?))""",
            (user_id, serial_number, 'ALL'))
        return cursor.fetchone() is not None

    def fetch_visible_serial_numbers(self, user_id):
        """Return list of serial numbers the given user_id has permission to see."""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT serial_number FROM HawkVisibility WHERE user_id = ? or user_id = ?""", (user_id, 'ALL'))
        serial_numbers = cursor.fetchall()
        cursor.execute("""SELECT serial_number FROM HawkOwnership WHERE user_id = ?""", (user_id,))
        owned_serial_number = cursor.fetchone()
        if owned_serial_number is not None:
            if owned_serial_number not in serial_numbers:
                serial_numbers.insert(0, owned_serial_number[0])
        return serial_numbers
    
    def add_notification(self, user_id, serial_number, hive_number, sensor, sign, value):
        """Add a notification to the database.
        
        :raises PermissionError: if user_id isn't the owner of the hawk 'serial_number'
        :raises ValueError: if sign isn't '>' or '<'"""
        if not self.check_hawk_ownership(user_id, serial_number):
            raise PermissionError
        try:
            if not (sign == ">" or sign == "<"):
                return ValueError
            with self.connection:
                self.connection.execute("""INSERT INTO Notifications VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                        (str(uuid.uuid4()), user_id, serial_number, hive_number, sensor, sign, float(value)))
        except sqlite3.IntegrityError:
            # Only occurs if the uuid4 isn't unique. Reattempting should fix this.
            self.add_notification(user_id, serial_number, hive_number, sensor, sign, value)
        
    def remove_notification(self, user_id, notification_id):
        """Remove a notification from the database.
        
        :raises PermissionError: if the notification doesn't belong to user_id."""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT user_id FROM Notifications WHERE notification_id = ?""", (notification_id, ))
        notification_user_id = cursor.fetchone()

        # If the notification doesn't exist, nothing needs to be done.
        if notification_user_id is None:
            return

        if user_id == notification_user_id[0]:
            with self.connection:
                self.connection.execute("""DELETE FROM Notifications WHERE notification_id = ?""", (notification_id,))
            return
        else:
            raise PermissionError
    
    def fetch_notifications(self, serial_number=None, user_id=None):
        """Return all notifications linked to the given serial_number or user_id.
        
        :param serial_number: Serial Number assigned by Digital Matter to the Hawk
        :param user_id: uuid of the user
        :raises ValueError: if both serial_number and user_id are None"""
        
        cursor = self.connection.cursor()
        if serial_number is not None:
            cursor.execute("""SELECT * FROM Notifications WHERE serial_number = ?""", (serial_number, ))
            return cursor.fetchall()
        elif user_id is not None:
            cursor.execute("""SELECT * FROM Notifications WHERE user_id = ?""", (user_id, ))
            return cursor.fetchall()
        else:
            raise ValueError
        
    def fetch_hawk_owner(self, serial_number):
        """Return the user object for the user than owns the hawk with the given serial_number."""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT user_id FROM HawkOwnership WHERE serial_number = ?""", (serial_number, ))
        return self.fetch_user(cursor.fetchone()[0])