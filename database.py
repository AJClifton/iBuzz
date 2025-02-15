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
                    'temperature_1', 'temperature_2', 'temperature_3', 'humidity', 'weight', 'accelerometer', 'bees_out', 'bees_in', 'frequency']

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
                                    humidity NUMERIC,
                                    weight NUMERIC,
                                    accelerometer   NUMERIC,
                                    bees_out INTEGER,
                                    bees_in INTEGER,
                                    frequency NUMERIC,
                                    PRIMARY KEY(serial_number, hive_number, time)
                                );""")
        self.replay_log = ReplayLog()

    def data_received(self, json, notification_method=None):
        """Run :func:'~database.Database._process_data' as a thread.
        
        :param notification_method: method that will be called after each hive is processed for notifications. Will be passed current_weather_station_data, current_hive_data, previous_weather_station_data, previous_hive_data."""
        thread = threading.Thread(target=self._process_data, args=[json, notification_method])
        thread.start()

    def _compare_and_add_hive(self, hives, new_hive):
        """Modify hives so that it contains only the most recent data for each hive_number.
        
        If a hive with the same hive_number already exists in hives, do not add new_hive.
        If a hive exists in hives which is an older version of new_hive, remove that hive."""
        older_version = False
        to_remove = []
        for hive in hives:
            if hive.is_more_recent_or_equal_to(new_hive):
                older_version = True
            if new_hive.is_more_recent_version_of(hive):
                to_remove.append(hive)
        if not older_version:
            hives.append(new_hive)
        for hive_to_remove in to_remove:
            hives.remove(hive_to_remove)
        return hives

    def _process_data(self, json, notification_method = None):
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
                                weather_station = WeatherStationData(serial_number, *encoded_data.extract_outside_humidity_and_temperature(tag.get("Data")))
                            except ValueError:
                                new_hive = HiveData(*encoded_data.extract_custom_data(tag.get("Data")))
                                new_hive.set_time(epoch_time)
                                hives = self._compare_and_add_hive(hives, new_hive)
                        except Exception as e:
                            error_logger.log_error(e)
                else:
                    data_str = field.get("Data", None)
                    if data_str is not None:
                        try:
                            try:
                                weather_station = WeatherStationData(serial_number, *encoded_data.extract_outside_humidity_and_temperature(data_str))
                            except ValueError:
                                new_hive = HiveData(*encoded_data.extract_custom_data(data_str))
                                new_hive.set_time(epoch_time)
                                hives = self._compare_and_add_hive(hives, new_hive)
                        except Exception as e:
                            error_logger.log_error(e)

        if notification_method is not None:
            all_previous_values = self.fetch_most_recent_values(serial_number)
        notification_method_arguments = []
        for hive in hives:
            try:
                if notification_method is not None:
                    # Throws KeyError if there aren't any previous values
                    previous_values = all_previous_values[str(hive.hive_number)]
                    previous_weather_station_data = WeatherStationData(serial_number, previous_values[1], previous_values[2])
                    previous_hive_data = HiveData(previous_values[4], previous_values[5], previous_values[6], previous_values[7], previous_values[8], previous_values[9], previous_values[10], previous_values[11], previous_values[12], previous_values[13])
                    notification_method_arguments.append((weather_station, hive, previous_weather_station_data, previous_hive_data))
            except KeyError:
                continue
        with self.connection:
            print(hives)
            for hive in hives:
                print("constraint values ", (weather_station.serial_number, hive.hive_number, hive.time))
                r = self.connection.execute("""SELECT * FROM Data WHERE serial_number = ? and hive_number = ? and time = ?""", (weather_station.serial_number, hive.hive_number, hive.time))
                print(r.fetchall())
                self.connection.execute(
                    "INSERT INTO Data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (*weather_station.get_data(), *hive.get_data()))
        if notification_method is not None:
            for arguments in notification_method_arguments:
                notification_method(*arguments)

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
            raise KeyError
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
        most_recent_values = {}
        cursor = self.connection.cursor()
        for hive_number in hive_numbers:
            cursor.execute("""SELECT * FROM Data WHERE serial_number = ? and hive_number = ? ORDER BY time DESC LIMIT 1""", (serial_number, hive_number))
            values = cursor.fetchone()
            if values is not None:
                most_recent_values[str(hive_number)] = values
        return most_recent_values

    def fetch_hive_numbers(self, serial_number):
        """Return all hive numbers associated with the given serial_number."""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT DISTINCT hive_number from Data WHERE serial_number = ?""", (serial_number, ))
        hive_numbers = []
        for line in cursor.fetchall():
            hive_numbers.append(line[0])
        return hive_numbers
    
    def data_to_csv(self, serial_number):
        """Return the text for a csv file that contains all the data linked to the given serial_number."""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM Data WHERE serial_number = ?""", (serial_number,))
        text = ""
        for line in cursor.fetchall():
            for part in line[:-1]:
                text += str(part) + ","
            text += str(line[-1]) + "\n"
        return text