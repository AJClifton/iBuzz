# import duckdb
import sqlite3
import os
import threading


class Database:
    database_path = "database.db"
    database_lock = threading.Lock()

    def __init__(self):
        if not os.path.isfile(self.database_path):
            pass
        self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
        if False:
            self.connection.execute("""CREATE TABLE Data (
                                    SerNo	INTEGER,
                                    SeqNo	INTEGER,
                                    DateTime	TEXT,
                                    Temp	NUMERIC,
                                    Humidity	NUMERIC,
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
            self.database_lock.acquire()

            self.connection.execute("INSERT INTO Data VALUES (?, ?, ?, ?, ?)", (ser_no, seq_no, date, 0, 0))
            self.connection.commit()

            self.database_lock.release()
            print(ser_no, seq_no, date)


if __name__ == "__main__":
    database = Database()
