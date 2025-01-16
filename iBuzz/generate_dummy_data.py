import random
import sqlite3
import time

db = sqlite3.connect("database.db")

""" serial_number	
    outside_humidity
    outside_temperature	
    time
    hive_number 
    temperature_1 
    temperature_2 
    temperature_3 
    accelerometer
    entrance 
    weight
    frequency """

serial_numbers = ["12345"]

number = 200
hives = 2

times = [int(time.time() - 2*number*60 + 60*i + random.randint(-10, 10)) for i in range(number)]
outside_temperatures = [round(random.randint(-5, 30) + (0.002 * i), 2) for i in range(number)]
outside_humidities = [round(random.random() / 2 + 0.5, 2) for i in range(number)]

for serial_number in serial_numbers:
    for i in range(len(outside_temperatures)):
        for j in range(hives):
            db.execute("INSERT INTO Data VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", 
                    (serial_number, outside_humidities[i], outside_temperatures[i], times[i], j, outside_temperatures[i] - random.randint(2, 4), 0,0,0,0,0,0))
db.commit()

db.close()
