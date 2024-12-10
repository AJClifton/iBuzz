# import duckdb
import calendar
import sqlite3
import os
import threading
import time
import encoded_data
import error_logger


class Database:
    database_lock = threading.Lock()

    column_names = ['serial_number', 'sequence_number', 'time', 'outside_temperature', 'outside_humidity',
                    'temperature_1', 'temperature_2', 'temperature_3', 'accelerometer', 'entrance', 'weight', 'frequency']

    def __init__(self, database_path="database.db"):
        """Manage a database used for storing sensor data.

        Creates and manages an SQLite database for storing sensor data.

        'serial_number' is assigned by Digital Matter and is unique to the Hawk.
        'sequence_number' increases every time the Hawk commits and provides a definitive order.
        'time' is the number of seconds since 1/1/1970.
        There are three internal temperature sensor slots available because that is the maximum allowed by this project's hardware.
        'entrance' is the number of bees going in and out of the hive.
        """
        self.database_path = database_path
        database_exists = os.path.isfile(self.database_path)
        self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
        if not database_exists:
            self.connection.execute("""CREATE TABLE Data (
                                    serial_number	INTEGER,
                                    sequence_number	INTEGER,
                                    time	INTEGER,
                                    outside_temperature	NUMERIC,
                                    outside_humidity	NUMERIC,
                                    temperature_1  NUMERIC,
                                    temperature_2  NUMERIC,
                                    temperature_3  NUMERIC,
                                    accelerometer   NUMERIC,
                                    entrance    INTEGER,
                                    weight  NUMERIC,
                                    frequency NUMERIC,
                                    PRIMARY KEY(serial_number, sequence_number)
                                );""")

    def data_received(self, json):
        """Run :func:'~database.Database._process_data' as a thread."""
        thread = threading.Thread(target=self._process_data, args=[json])
        thread.start()

    def _process_data(self, json):
        """Extract and store the data values in the JSON from the Hawk."""
        serial_number = json["SerNo"]
        for record in json["Records"]:
            sequence_number = record["SeqNo"]
            date = record["DateUTC"]
            epoch_time = calendar.timegm(time.strptime(date, '%Y-%m-%d %H:%M:%S'))
            outside_humidity, outside_temperature = None, None
            temperature_1 = 0

            # Data can be in one of two places
            # { "Records": [{ "Fields": [{ "Tags": [{"Data": data}] }] }] } or
            # { "Records": [{ "Fields": [{ "Data": data}] }] }
            for field in record["Fields"]:
                tags = field.get("Tags", None)
                if tags is not None:
                    for tag in tags:
                        try:
                            try:
                                outside_humidity, outside_temperature = encoded_data.extract_outside_humidity_and_temperature(tag.get("Data"))
                            except ValueError:
                                temperature_1 = encoded_data.extract_custom_data(tag.get("Data"))
                        except Exception as e:
                            error_logger.log_error(e)
                else:
                    data_str = field.get("Data", None)
                    if data_str is not None:
                        try:
                            try:
                                outside_humidity, outside_temperature = encoded_data.extract_outside_humidity_and_temperature(data_str)
                            except ValueError:
                                temperature_1 = encoded_data.extract_custom_data(data_str)
                        except Exception as e:
                            error_logger.log_error(e)

            with self.database_lock.acquire():
                self.connection.execute(
                    "INSERT INTO Data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (serial_number, sequence_number, epoch_time, outside_temperature, outside_humidity, temperature_1, 0, 0, 0, 0, 0, 0))
                self.connection.commit()

    def fetch_field(self, serial_number, field, start_time=0, end_time=None):
        """Return the time column and the given column.

        Return the time column and the given field column between start_time and end_time.
        :param serial_number: Serial Number assigned by Digital Matter to the Hawk
        :param str field: column to fetch
        :type start_time: int
        :type end_time: int or None
        :raises KeyError: if field isn't a database column"""
        end_time = time.time() if end_time is None else end_time
        if field not in self.column_names:
            raise Exception(KeyError)
        cursor = self.connection.cursor()
        cursor.execute("""SELECT time, ? FROM Data WHERE serial_number = ? and time > ? and time < ?""",
                       (field, serial_number, start_time, end_time))
        data = {'Time': [], str(field): []}
        for line in cursor.fetchall():
            data['Time'].append(line[0])
            data[field].append(line[1])
        cursor.close()
        return data

    def fetch_names(self):
        """Returns the column names for the Data table."""
        return self.column_names


if __name__ == "__main__":
    database = Database()
