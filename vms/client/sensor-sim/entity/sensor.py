import random
import math


class Sensor:
    def __init__(self, name: str):
        self.name = name
        self.value = 0.0
        self.type = "sensor"

    def generate_new_value(self):
        raise NotImplementedError

    def get_data(self):
        return float(self.value)


class Temperature(Sensor):
    # Температура: 20..80 °C
    def __init__(self, name: str):
        super().__init__(name)
        self.type = "temperature"

    def generate_new_value(self):
        self.value = round(random.uniform(20.0, 80.0), 2)


class Pressure(Sensor):
    # Давление: 1.0..10.0 bar
    def __init__(self, name: str):
        super().__init__(name)
        self.type = "pressure"

    def generate_new_value(self):
        birth_year = 2003  # <-- вставь свой год рождения (по требованию доп. задания)
        base = random.uniform(1.0, 10.0)
        self.value = round(base + (birth_year % 10) * 0.01, 3)


class Current(Sensor):
    # Ток: синусоида примерно -5..5 A
    def __init__(self, name: str):
        super().__init__(name)
        self.type = "current"
        self.step = 0

    def generate_new_value(self):
        self.value = round(5 * math.sin(self.step / 5), 3)
        self.step += 1


class Humidity(Sensor):
    # Влажность: 30..90 %
    def __init__(self, name: str):
        super().__init__(name)
        self.type = "humidity"

    def generate_new_value(self):
        self.value = round(random.uniform(30.0, 90.0), 2)