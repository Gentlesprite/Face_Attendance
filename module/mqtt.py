# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/27 12:31
# File:mqtt.py
from typing import Union, List

import paho.mqtt.client as mqtt

from module import log


class MQTTClient:
    def __init__(
            self,
            ip: str,
            port: int,
            topic: Union[str, List[str]],
            username: str,
            password: str,
            client_id: str = 'pi-mqtt-client',
            main_loop: bool = False
    ):
        self.ip: str = ip
        self.port: int = port
        self.topic = topic
        self.client_id: str = client_id
        self.client = mqtt.Client(client_id=self.client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(username, password)
        self.__config_callback()
        self.__add_topic()
        self.__connect()
        self.client.loop_forever() if main_loop else self.client.loop_start()

    def __config_callback(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def __connect(self):
        try:
            if self.client.connect(self.ip, self.port, 60) == 0:
                log.info('连接MQTT服务器成功。')
                self.__add_topic()
                log.info(
                    f'"{self.client_id}"新增订阅主题:{",".join(self.topic) if isinstance(self.topic, list) else self.topic}。')
            else:
                raise ConnectionError('Failed to connect to MQTT server.')

        except (Exception, ConnectionError) as e:
            log.error(f'连接MQTT服务器失败,请检查配置文件或服务器状态,原因:"{e}"')

    def __add_topic(self):
        if isinstance(self.topic, str):
            self.client.subscribe(self.topic)
        elif isinstance(self.topic, list):
            for t in self.topic:
                self.client.subscribe(t)

    @staticmethod
    def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            log.error(f'连接MQTT服务器失败,错误码:"{reason_code}"')

    @staticmethod
    def on_message(client, userdata, message):
        log.info(f'[Topic]:{message.topic} [Message]:{message.payload.decode()}')


if __name__ == '__main__':
    mqtt = MQTTClient(
        ip='10.10.10.106',
        port=1883,
        topic=['test', 'test2', 'test3', 'test4'],
        username='admin',
        password='public',
        client_id='pi-lzy',
        main_loop=True
    )
