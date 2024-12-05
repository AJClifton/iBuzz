# import duckdb
import calendar
import sqlite3
import os
import threading
import time
import encoded_data


class Database:
    database_path = "database.db"
    database_lock = threading.Lock()

    column_names = ['SerNo', 'SeqNo', 'Time', 'Outside_temp', 'Outside_humidity', 'Temp_1', 'Temp_2', 'Temp_3',
                    'Accelerometer', 'Entrance', 'Weight', 'Frequency']
    readable_column_names = ['Serial Number', 'Sequence Number', 'Time', 'Outside Temperature', 'Outside Humidity',
                    'Temperature 1', 'Temperature 2', 'Temperature 3', 'Accelerometer', 'Entrance', 'Weight', 'Frequency']

    def __init__(self):
        database_exists = os.path.isfile(self.database_path)
        self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
        if not database_exists:
            self.connection.execute("""CREATE TABLE Data (
                                    SerNo	INTEGER,
                                    SeqNo	INTEGER,
                                    Time	INTEGER,
                                    Outside_temp	NUMERIC,
                                    Outside_humidity	NUMERIC,
                                    Temp_1  NUMERIC,
                                    Temp_2  NUMERIC,
                                    Temp_3  NUMERIC,
                                    Accelerometer   NUMERIC,
                                    Entrance    INT,
                                    Weight  NUMERIC,
                                    Frequency NUMERIC,
                                    PRIMARY KEY(SerNo,SeqNo)
                                );""")

    def data_received(self, json):
        thread = threading.Thread(target=self.__process_data, args=[json])
        thread.start()

    def __process_data(self, json):
        ser_no = json["SerNo"]
        for record in json["Records"]:
            seq_no = record["SeqNo"]
            date = record["DateUTC"]
            epoch_time = calendar.timegm(time.strptime(date, '%Y-%m-%d %H:%M:%S'))
            temp_1 = 0

            # Not all field entries contain the data needed - looking for 'Tags' key
            outside_humidity, outside_temperature = None, None
            for field in record["Fields"]:
                data_dict = field.get("Tags", None)
                if data_dict is not None:
                    for tag in data_dict:
                        try:
                            outside_humidity, outside_temperature = encoded_data.extract_ela_rht_data(tag.get("Data"))
                        except ValueError:
                            temp_1 = encoded_data.extract_custom_data(tag.get("Data"))
                        except Exception as e:
                            pass
                data_str = field.get("Data", None)
                if data_str is not None:
                    try:
                        outside_humidity, outside_temperature = encoded_data.extract_ela_rht_data(data_str)
                    except ValueError:
                        temp_1 = encoded_data.extract_custom_data(data_str)


            if outside_temperature is None:
                continue

            self.database_lock.acquire()
            self.connection.execute("INSERT INTO Data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (ser_no, seq_no, epoch_time, outside_temperature, outside_humidity, temp_1, 0, 0, 0, 0, 0, 0))
            self.connection.commit()
            self.database_lock.release()

    def fetch_data(self, field, start_time=0, end_time=None):
        end_time = time.time() if end_time is None else end_time
        if field not in self.column_names:
            return {}
        cursor = self.connection.cursor()
        cursor.execute(f"""SELECT Time, {field} FROM Data WHERE Time > ?""", (start_time,))
        data = {'Time': [], str(field): []}
        for line in cursor.fetchall():
            data['Time'].append(line[0])
            data[field].append(line[1])
        cursor.close()
        return data

    def fetch_names(self):
        return {'names': self.column_names, 'readable_names': self.readable_column_names}



if __name__ == "__main__":
    database = Database()
