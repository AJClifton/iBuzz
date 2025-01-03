import smtplib


class Notifications:


    def __init__(self, gmail, password, login_db):
        self.from_email = gmail
        self.smtp = smtplib.SMTP('smtp.gmail.com', 587)
        self.smtp.starttls()
        self.smtp.login(self.from_email, password)
        self.login_db = login_db


    def send_email_notification(self, recipient, subject, message):
        """Send an email to the given recipient.
        
        :param str recipient: recipient's email address"""
        email = f"""From: {self.from_email}\nTo: {recipient}\nSubject: {subject}\n\n{message}"""
        self.smtp.sendmail(self.from_email, recipient, email)


    def evaluate(self, current_weather_station_data, current_hive_data, previous_weather_station_data, previous_hive_data):
        """Check if any of the current data given meet the requirements for a notification and the previous values don't and send a notification if this is the case."""
        serial_number = current_weather_station_data.serial_number
        notifications = self.login_db.fetch_notifications(serial_number=serial_number)
        if len(notifications) == 0:
            return
        for notification in notifications:
            user = self.login_db.fetch_user(notification[1])
            hive_number, sensor, sign, value = notification[3], notification[4], notification[5], notification[6]
            print(hive_number, sensor, sign, value)
            # There may be a better way to do this... perhaps this should be in the HiveData classes.
            if sensor == "outside_temperature":
                current_sensor_value = current_weather_station_data.outside_temperature
                previous_sensor_value = previous_weather_station_data.outside_temperature
            elif sensor == "outside_humidity":
                current_sensor_value = current_weather_station_data.outside_humidity
                previous_sensor_value = previous_weather_station_data.outside_humidity
            elif sensor == "temperature_1":
                current_sensor_value = current_hive_data.temperature_1
                previous_sensor_value = previous_hive_data.temperature_1
            elif sensor == "temperature_2":
                current_sensor_value = current_hive_data.temperature_2
                previous_sensor_value = previous_hive_data.temperature_2
            elif sensor == "temperature_3":
                current_sensor_value = current_hive_data.temperature_3
                previous_sensor_value = previous_hive_data.temperature_3
            elif sensor == "humidity":
                current_sensor_value = current_hive_data.humidity
                previous_sensor_value = previous_hive_data.humidity
            elif sensor == "weight":
                current_sensor_value = current_hive_data.weight
                previous_sensor_value = previous_hive_data.weight
            elif sensor == "accelerometer":
                current_sensor_value = current_hive_data.accelerometer
                previous_sensor_value = previous_hive_data.accelerometer
            elif sensor == "bees_out":
                current_sensor_value = current_hive_data.bees_out
                previous_sensor_value = previous_hive_data.bees_out
            elif sensor == "bees_in":
                current_sensor_value = current_hive_data.bees_in
                previous_sensor_value = previous_hive_data.bees_in
            elif sensor == "frequency":
                current_sensor_value = current_hive_data.frequency
                previous_sensor_value = previous_hive_data.frequency
            else:
                continue
            print(hive_number, sensor, sign, value, current_sensor_value, previous_sensor_value, user.email)
            if sign == ">" and current_sensor_value > value and not previous_sensor_value > value:
                    self.send_email_notification(user.email, f"iBuzz ALERT {sensor}", f"{sensor} in hive '{serial_number} - {hive_number}' was detected at {current_sensor_value} which is greater than your threshold of {value}")
                    continue
            if sign == "<" and current_sensor_value < value and not previous_sensor_value < value:
                    self.send_email_notification(user.email, f"iBuzz ALERT {sensor}", f"{sensor} in hive '{serial_number} - {hive_number}' was detected at {current_sensor_value} which is lower than your threshold of {value}")
                    continue
            
