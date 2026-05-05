import time
from os import environ

import paho.mqtt.client as paho

from entity.sensor import Temperature, Pressure, Current, Humidity

broker = environ.get("SIM_HOST", "localhost")
port = int(environ.get("SIM_PORT", "1883"))
name = environ.get("SIM_NAME", "sensor")
period = int(environ.get("SIM_PERIOD", "1"))
type_sim = environ.get("SIM_TYPE", "temperature")

sensors = {
    "temperature": Temperature,
    "pressure": Pressure,
    "current": Current,
    "humidity": Humidity
}


def on_publish(client, userdata, mid):
    print(f"[PUBLISH] message_id={mid}")


if type_sim not in sensors:
    raise ValueError(f"Unknown SIM_TYPE: {type_sim}. Available: {list(sensors.keys())}")

sensor = sensors[type_sim](name=name)

client = paho.Client(sensor.name)
client.on_publish = on_publish
client.connect(broker, port)

print(f"Started sensor: {sensor.name} type={sensor.type} broker={broker}:{port} period={period}s")

while True:
    sensor.generate_new_value()
    topic = f"sensors/{sensor.type}/{sensor.name}"
    value = sensor.get_data()

    client.publish(topic, value)
    print(f"[SEND] {topic} -> {value}")

    time.sleep(period)