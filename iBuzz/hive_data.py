

class HiveData:

    def __init__(self, hive_number, temperature_1, temperature_2, temperature_3, humidity, weight, accelerometer, bees_out, bees_in, frequency):
        self.hive_number = hive_number
        self.temperature_1 = temperature_1
        self.temperature_2 = temperature_2
        self.temperature_3 = temperature_3
        self.humidity = humidity
        self.weight = weight
        self.accelerometer = accelerometer
        self.bees_out = bees_out
        self.bees_in = bees_in
        self.frequency = frequency

    def set_time(self, time):
        self.time = time

    def is_more_recent_version_of(self, other_hive):
        """Return True if the main HiveData has the same hive_number and a more recent time than other_hive."""
        return self.time > other_hive.time and self.hive_number == other_hive.hive_number
    
    def is_more_recent_or_equal_to(self, other_hive):
        """Return True if the main HiveData has the same hive_number and a more recent or identical time to other_hive."""
        return self.time >= other_hive.time and self.hive_number == other_hive.hive_number


    def get_data(self):
        if self.temperature_2 is None:
            return (self.time, self.hive_number, self.temperature_1)
        return (self.time, self.hive_number, self.temperature_1, self.temperature_2, self.temperature_3, self.humidity, self.weight, self.accelerometer, self.bees_out, self.bees_in, self.frequency)

    

class WeatherStationData:

    def __init__(self, serial_number, outside_humidity, outside_temperature):
        self.serial_number = serial_number
        self.outside_humidity = outside_humidity
        self.outside_temperature = outside_temperature

    def get_data(self):
        return (self.serial_number, self.outside_humidity, self.outside_temperature)

