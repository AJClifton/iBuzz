# import duckdb
import calendar
import sqlite3
import os
import threading
import time
import encoded_data
import error_logger
from replay_log import ReplayLog
from hive_data import WeatherStationData, HiveData


class Database:
    database_lock = threading.Lock()

    column_names = ['serial_number', 'outside_humidity', 'outside_temperature', 'time', 'hive_number',
                    'temperature_1', 'temperature_2', 'temperature_3', 'accelerometer', 'entrance', 'weight', 'frequency']

    def __init__(self, database_path="database.db"):
        """Manage a database used for storing sensor data.

        Creates and manages an SQLite database for storing sensor data.

        'serial_number' is assigned by Digital Matter and is unique to the Hawk.
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
                                    outside_humidity	NUMERIC,
                                    outside_temperature	NUMERIC,
                                    time	INTEGER,
                                    hive_number INTEGER,
                                    temperature_1  NUMERIC,
                                    temperature_2  NUMERIC,
                                    temperature_3  NUMERIC,
                                    accelerometer   NUMERIC,
                                    entrance    INTEGER,
                                    weight  NUMERIC,
                                    frequency NUMERIC,
                                    PRIMARY KEY(serial_number, hive_number, time)
                                );""")
        self.replay_log = ReplayLog()

    def data_received(self, json):
        """Run :func:'~database.Database._process_data' as a thread."""
        thread = threading.Thread(target=self._process_data, args=[json])
        thread.start()

    def _compare_and_add_hive(self, hives, new_hive):
        """Modify hives so that it contains only the most recent data for each hive_number.
        
        If a hive with the same hive_number already exists in hives, do not add new_hive.
        If a hive exists in hives which is an older version of new_hive, remove that hive."""
        older_version = False
        to_remove = []
        for hive in hives:
            if hive.is_more_recent_version_of(new_hive):
                older_version = True
            if new_hive.is_more_recent_version_of(hive):
                to_remove.append(hive)
        if not older_version:
            hives.append(new_hive)
        for hive_to_remove in to_remove:
            hives.remove(hive_to_remove)
        return hives

    def _process_data(self, json):
        """Extract and store the data values in the JSON from the Hawk."""
        try:
            serial_number = json["SerNo"]
            self.replay_log.add_to_log(serial_number, json)
        except:
            self.replay_log.add_to_log("error", json)
            print("Error determining serial_number: ", json)
        weather_station = None
        hives = []
        for record in json["Records"]:
            date = record["DateUTC"]
            time = calendar.timegm(record['DateUTC'].strptime(date, '%Y-%m-%d %H:%M:%S'))
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
                                weather_station = WeatherStationData(*encoded_data.extract_outside_humidity_and_temperature(tag.get("Data")))
                            except ValueError:
                                new_hive = HiveData(*encoded_data.extract_custom_data(tag.get("Data")))
                                new_hive.set_time(time)
                                hives = self._compare_and_add_hive(hives, new_hive)
                        except Exception as e:
                            error_logger.log_error(e)
                else:
                    data_str = field.get("Data", None)
                    if data_str is not None:
                        try:
                            try:
                                weather_station = WeatherStationData(*encoded_data.extract_outside_humidity_and_temperature(data_str))
                            except ValueError:
                                new_hive = HiveData(*encoded_data.extract_custom_data(data_str))
                                new_hive.set_time(time)
                                hives = self._compare_and_add_hive(hives, new_hive)
                        except Exception as e:
                            error_logger.log_error(e)

            with self.connection():
                for hive in hives:
                    self.connection.execute(
                        "INSERT INTO Data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (*weather_station.get_data(), *hive.get_data(), 0, 0, 0, 0, 0, 0))

    def fetch_field(self, serial_number, hive_number, field, start_time=0, end_time=None):
        """Return the time column and the given column.

        Return the time column and the given field column between start_time and end_time.
        :param serial_number: Serial Number assigned by Digital Matter to the Hawk
        :param str field: column to fetch
        :type start_time: int
        :type end_time: int or None
        :raises KeyError: if field isn't a database column"""
        end_time = time.time() if end_time is None else end_time
        # Validate the field value to prevent SQL injections
        if field not in self.column_names:
            raise Exception(KeyError)
        cursor = self.connection.cursor()
        cursor.execute(f"""SELECT time, {field} FROM Data WHERE serial_number = ? and hive_number = ? and time > ? and time < ? ORDER BY time ASC""",
                       (serial_number, hive_number, start_time, end_time))
        data = {'time': [], str(field): []}
        for line in cursor.fetchall():
            data['time'].append(line[0])
            data[str(field)].append(line[1])
        cursor.close()
        return data

    def fetch_names(self):
        """Returns the column names for the Data table."""
        return self.column_names
    
    def fetch_most_recent_values(self, serial_number):
        """Return the most recent values for each hive_number belonging to the given serial_number."""
        hive_numbers = self.fetch_hive_numbers(serial_number)
        most_recent_values = []
        cursor = self.connection.cursor()
        for hive_number in hive_numbers:
            cursor.execute("""SELECT * FROM Data ORDER BY time DESC LIMIT 1 WHERE serial_number = ? and hive_number = ?""", (serial_number, hive_number))
            values = cursor.fetchone()
            if values is not None:
                most_recent_values.append({'hive_number': hive_number, 'values':values})
        return most_recent_values

    def fetch_hive_numbers(self, serial_number):
        """Return all hive numbers associated with the given serial_number."""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT DISTINCT hive_number from Data WHERE serial_number = ?""", (serial_number, ))
        hive_numbers = []
        for line in cursor.fetchall():
            hive_numbers.append(line[0])
        return hive_numbers