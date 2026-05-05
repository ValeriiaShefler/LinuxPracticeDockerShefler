# ОТЧЕТ ПО ЗАДАНИЮ DockerPractice ШЕФЛЕР
## Налаживание маршрутов
При попытке установить docker и docker compose я столкнулась с ошибкой конфликтов маршрутизации при попытке доступа в интернет:  
    ![Проблема с доступом к интернету](assets/images/1_network_issue.png)
    ![Проверка routs](assets/images/2_check_routs.png)  
Устраним конфликт маршрутизации. На на машине LinuxA изменим конфигурационный файл сети:  
    ![Netplan_A](assets/images/3_netplan_A.png)  
Проверим доступ в интернет:  
    ![Check_inet_A](assets/images/4_check_A.png)  
А также на машине LinuxC:  
    ![Netplan_C](assets/images/5_netplan_C.png)  
Проверим доступ в интернет:  
    ![Check_inet_C](assets/images/6_check_C.png)  
Теперь проверим, что не нарушили общую работу сети, налаженной в первой работе:  
    ![Проверяем ненарушенность первой лабы](assets/images/7_check_lab_1.png)
    ![Проверяем ненарушенность первой лабы](assets/images/8_check_lab_1_1.png)
Таким образом, убран конфликт маршрутизации через удаление gateway4 на внутренних интерфейсах (servernet/clientnet) на машинах LinuxA и LinuxC, чтобы они не создавали лишний default route, а вместо этого прописали статические маршруты к противоположной подсети через шлюз LinuxB (192.168.16.1 / 192.168.3.1). Благодаря этому интернет стабильно работает через интерфейс с DHCP (enp0s3), а обмен данными между подсетями по-прежнему проходит строго через шлюз.  

## 1. Установка docker и docker compose
На каждую из машин (LinuxA, LinuxB, LinuxC) утановим docker и docker compose (рассматривать будем на примере установки для LinuxA):  

Сначала произведем непосредственную установку docker:  
    ![Установка докер1](assets/images/9_setup_docker_1.png)
    ![Установка докер1](assets/images/10_setup_docker_2.png)  
Запустим и установим автозапуск docker:  
    ![Запуск докер](assets/images/11_docker_on.png)
Добавим пользователя в docker группу:  
    ![Добавление пользователя в докер группу](assets/images/12_docker_group.png)  
Проверим работу docker:  
    ![Проверка докер](assets/images/13_docker_check.png)  
Произведем также установку docker compose:  
    ![Установка докер-компоуз](assets/images/14_docker_compose_setup.png)  
Проверим:  
    ![Установка докер-компоуз](assets/images/15_docker_compose_setup_check.png)  
Произведем финальную проверку:  
    ![Проверка докер окончательная](assets/images/16_docker_last_check.png)
## 2. Проверим наличие сети между машинами:  
    ![ ](assets/images/17_test_net_A.png)
    ![ ](assets/images/18_test_net_A.png)
    ![ ](assets/images/19_test_net_A.png)

## 3. Разработка скриптов для машины LinuxA:  
Проект имеет следующую структру:  

sensor-sim/
│   main.py
│   requirements.txt
│   Dockerfile
└── entity/
    │   __init__.py
    └── sensor.py

 Рассмотрим содержание каждого из файлов  

 ### 3.1. Сенсоры  
 В папке находятся файлы, описывающие классы различных датчиков. В файле sensor.py находится описание базового класса датчика, чьи характеристики наследуются конретными датчиками, также описанными в файле:  

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

## 3.2. main.py
main.py — это точка входа программы, которая решает какой именно датчик запускать, исходя из переменной среды. В случае, если она не задана, то по умолчанию программа считает, что это датчик температуры:  

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

## 3.3. Dockerfile  
    FROM python:alpine3.19

    WORKDIR /app

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . .

    CMD ["python", "main.py"]  

## 3.4. requirements.txt  
    paho_mqtt==1.6.1  

# 4. Настройка деплоя  
Для данных целей я использовала VS Code Remote SSH вместо PyCharm, ведь в основном работаю через VS Code. Для этого в VS Code устанавливаем соотвествующее расширение и непосредственно настраиваем подключение:  
    ![ ](assets/images/20_remote_ssh_1.png)  
    ![ ](assets/images/21_remote_ssh_2.png)  
    ![ ](assets/images/22_remote_ssh_3.png)  
    ![ ](assets/images/23_remote_ssh_4.png)  
Перенесем проект на машину LinuxA:  
    ![ ](assets/images/24_grab_project_1.png)  
    ![ ](assets/images/25_grab_project_2.png)  
Произведем ряд проверок, в том числе поменяем файл main.py временно добавив строку печати и посмотрим, отразится ли это на самой машине:  
    ![ ](assets/images/26_deploy_check.png)  
    ![ ](assets/images/27_deploy_check.png)  
    ![ ](assets/images/28_deploy_check.png)  
    ![ ](assets/images/29_deploy_check.png)  
Папка sensor-sim на машине LinuxA расположена по адресу /home/shefler_1/DockerPractice/client/sensor-sim.

# 5. Создание образа docker  
Произведем сборку docker-образа и проверим:  
    ![ ](assets/images/32_build_docker_view.png)  
    ![ ](assets/images/33_build_docker_check.png)  

# 6. Настройка mosquitto на LinuxB
    ![ ](assets/images/34_mosquitto_1.png)  
    ![ ](assets/images/35_mosquitto_2.png)  
    ![ ](assets/images/36_mosquitto_3.png)  
    ![ ](assets/images/37_mosquitto_4.png)  

# 7. Запуск контейнера на LinuxA:  
Запустим контейнер:  
    ![ ](assets/images/38_docker_run.png)
Запушим:  
    ![ ](assets/images/39_dockerA_push.png)  

# 8. Запуск через docker-compose шести сенсоров  
Создадим docker-compose.yml файл:  
    version: "3"

    services:
    temp1:
        image: sheflervaleriia/sensor-sim
        environment:
        - SIM_HOST=192.168.0.107
        - SIM_NAME=temp1
        - SIM_PERIOD=2
        - SIM_TYPE=temperature

    temp2:
        image: sheflervaleriia/sensor-sim
        environment:
        - SIM_HOST=192.168.0.107
        - SIM_NAME=temp2
        - SIM_PERIOD=3
        - SIM_TYPE=temperature

    pressure1:
        image: sheflervaleriia/sensor-sim
        environment:
        - SIM_HOST=192.168.0.107
        - SIM_NAME=pressure1
        - SIM_PERIOD=4
        - SIM_TYPE=pressure

    pressure2:
        image: sheflervaleriia/sensor-sim
        environment:
        - SIM_HOST=192.168.0.107
        - SIM_NAME=pressure2
        - SIM_PERIOD=5
        - SIM_TYPE=pressure

    current1:
        image: sheflervaleriia/sensor-sim
        environment:
        - SIM_HOST=192.168.0.107
        - SIM_NAME=current1
        - SIM_PERIOD=1
        - SIM_TYPE=current

    humidity1:
        image: sheflervaleriia/sensor-sim
        environment:
        - SIM_HOST=192.168.0.107
        - SIM_NAME=humidity1
        - SIM_PERIOD=3
        - SIM_TYPE=humidity  

Запускаем и проверяем:  
    ![ ](assets/images/40_docker_compose_A_check.png)  
    ![ ](assets/images/41_docker_compose_A_check.png)  

# 9. Проведем проверку через mqtt explorer:  
![ ](assets/images/42_mqtt_check.png)

# 10. Работа с Linux C  
Создадим скелет проекта:  
    ![ ](assets/images/43_create_skeleton_1.png)  
    ![ ](assets/images/44_create_skeleton_2.png)  
init-скрипт для InfluxDB:  
    ![ ](assets/images/45_influx--init.iql.png)
Создаём docker-compose.yml:  

    version: "3"

    services:
    influxdb:
        image: influxdb:1.8
        container_name: influxdb
        volumes:
        - ./influxdb/scripts:/docker-entrypoint-initdb.d
        - influx_data:/var/lib/influxdb
        ports:
        - "8086:8086"
        networks:
        - server-net

    telegraf:
        image: telegraf
        container_name: telegraf
        volumes:
        - ./telegraf:/etc/telegraf:ro
        restart: unless-stopped
        networks:
        - server-net

    grafana:
        image: grafana/grafana
        container_name: grafana
        ports:
        - "3000:3000"
        volumes:
        - grafana_data:/var/lib/grafana
        - ./grafana/provisioning:/etc/grafana/provisioning
        environment:
        - GF_SECURITY_ADMIN_USER=admin
        - GF_SECURITY_ADMIN_PASSWORD=admin
        depends_on:
        - influxdb
        networks:
        - server-net
        restart: unless-stopped

    volumes:
    influx_data: {}
    grafana_data: {}

    networks:
    server-net: {}  

Сгенерируем базовый telegraf.conf:  
    ![ ](assets/images/46_telegraf.conf_base.png)  
        
Внесем раяд изменений в полученный конфигурационный файл:  
    ![ ](assets/images/47_telegraf.conf_change.png)  
    ![ ](assets/images/48_telegraf.conf_change.png)  
Запуск системы:  
    ![ ](assets/images/49_power_up.png)  
Проверим:  
    ![ ](assets/images/50_power_up_check.png)  
    ![ ](assets/images/51_power_up_check.png)  
Откроем garafana в браузере и подключим InfluxDB:  
    ![ ](assets/images/52_grafana_inet.png)  
    ![ ](assets/images/53_grafana_inet.png)  
Заполним поля:  
    URL: http://influxdb:8086  
    Database: sensors  
    Basic auth = ON  
    User: telegraf  
    Password: telegraf  
    ![ ](assets/images/54_grafana_inet.png)  
Создаем dashboard c графиками значений и их средних для всех сенсоров:  
    ![ ](assets/images/55_dash_board.png)  
Проверяем volumes Grafana:  
    ![ ](assets/images/56_test_dashboard.png)  
Проверим, что при удалении контейнера ничего не пропадет:  
    ![ ](assets/images/57_test_dashboard.png)  
    ![ ](assets/images/58_test_dashboard.png)  
# 11. ПРОВЕРКА  
Цель проверки: проверить, что система: поднимается из нуля → сама конфигурируется → показывает данные → без ручных действий   

Отсановим систему на LinuxC:  
    ![ ](assets/images/59_test_check.png)  
Поднимем все заново:  
    ![ ](assets/images/60_test_check.png)  
Проверим сеть:  
    ![ ](assets/images/61_net_check.png)  
Проверим influxdb:  
    ![ ](assets/images/62_influx_check.png)  
Как видим mqtt_consumer на месте.  

Проверим telegraf, как види подключение к MQTT есть:  
    ![ ](assets/images/63_telegraf_check.png)  
Однако, пропал дашборд в Grafna, что требует починки. В папке datasources создадим default.yaml:  

    apiVersion: 1

    datasources:
    - name: InfluxDB_v1
        type: influxdb
        access: proxy
        database: sensors
        user: telegraf
        url: http://influxdb:8086
        jsonData:
        httpMode: GET
        secureJsonData:
        password: telegraf
        isDefault: true  

А в папке dashboards другой default.yaml:  

    apiVersion: 1

    providers:
    - name: 'mqtt'
        orgId: 1
        folder: ''
        type: file
        disableDeletion: false
        editable: true
        options:
        path: /etc/grafana/provisioning/dashboards  

Теперь положим JSON dashboard в соотвествсующую папку:  
    ![ ](assets/images/64_export_dashboards.png)  
    ![ ](assets/images/65_export_dashboards.png)  
Пересоздадим систему командами docker-compose down -v и
docker-compose up -d и проверим, что dashboard не пропал:  
    ![ ](assets/images/66_yay.png)  
Действительно, теперь графики не пропадают.  

Внесем еще ряд изменений, создадим docker-compose файл для машины B:  
    version: "3"

    services:
    mosquitto:
        image: eclipse-mosquitto
        container_name: mosquitto
        restart: always
        ports:
        - "1883:1883"
        volumes:
        - ./mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf  
Изменим аналогичный файл на  машине A:  
     version: "3"

    services:
    temp1:
        image: ${DOCKERHUB_USERNAME}/sensor-sim:latest
        environment:
        - SIM_HOST=${MQTT_BROKER_HOST}
        - SIM_PORT=${MQTT_BROKER_PORT}
        - SIM_NAME=temp1
        - SIM_PERIOD=2
        - SIM_TYPE=temperature

    temp2:
        image: ${DOCKERHUB_USERNAME}/sensor-sim:latest
        environment:
        - SIM_HOST=${MQTT_BROKER_HOST}
        - SIM_PORT=${MQTT_BROKER_PORT}
        - SIM_NAME=temp2
        - SIM_PERIOD=3
        - SIM_TYPE=temperature

    pressure1:
        image: ${DOCKERHUB_USERNAME}/sensor-sim:latest
        environment:
        - SIM_HOST=${MQTT_BROKER_HOST}
        - SIM_PORT=${MQTT_BROKER_PORT}
        - SIM_NAME=pressure1
        - SIM_PERIOD=4
        - SIM_TYPE=pressure

    pressure2:
        image: ${DOCKERHUB_USERNAME}/sensor-sim:latest
        environment:
        - SIM_HOST=${MQTT_BROKER_HOST}
        - SIM_PORT=${MQTT_BROKER_PORT}
        - SIM_NAME=pressure2
        - SIM_PERIOD=5
        - SIM_TYPE=pressure

    current1:
        image: ${DOCKERHUB_USERNAME}/sensor-sim:latest
        environment:
        - SIM_HOST=${MQTT_BROKER_HOST}
        - SIM_PORT=${MQTT_BROKER_PORT}
        - SIM_NAME=current1
        - SIM_PERIOD=1
        - SIM_TYPE=current

    humidity1:
        image: ${DOCKERHUB_USERNAME}/sensor-sim:latest
        environment:
        - SIM_HOST=${MQTT_BROKER_HOST}
        - SIM_PORT=${MQTT_BROKER_PORT}
        - SIM_NAME=humidity1
        - SIM_PERIOD=3
        - SIM_TYPE=humidity

Также добавим файл .env на машину Linux A:  
    MQTT_BROKER_HOST=192.168.X.X   # IP VM B !!!
    MQTT_BROKER_PORT=1883
    DOCKERHUB_USERNAME=sheflervaleriia

Ссылка на docker-hub: https://hub.docker.com/repository/docker/sheflervaleriia/sensor-sim/general

Аналогично поступим и с машиной С, создадим .env файл с информацией, которую при необходимости можно будет быстро изменить:  
    MQTT_HOST=192.168.X.X
    MQTT_PORT=1883
    INFLUX_HOST=influxdb
    INFLUX_PORT=8086
    INFLUX_DB=sensors
    INFLUX_USER=telegraf
    INFLUX_PASS=telegraf  

Тогда в telegraf.conf:  
    [[inputs.mqtt_consumer]]
    servers = ["tcp://${MQTT_HOST}:${MQTT_PORT}"]
    topics = ["sensors/#"]
    data_format = "value"
    data_type = "float"

А в docker-compose.yml изменим:  
  telegraf:
    image: telegraf
    container_name: telegraf
    env_file:
      - .env
    volumes:
      - ./telegraf:/etc/telegraf:ro
    restart: unless-stopped
    networks:
      - server-net
