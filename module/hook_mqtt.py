# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/27 17:11
# File:hook_mqtt.py
from module.mqtt import MQTTClient


class HookMQTTClient(MQTTClient):
    def __init__(self, ip: str, port: int, topic: str, username: str, password: str, client_id: str):
        super().__init__(ip, port, topic, username, password, client_id)

    @staticmethod
    def on_message(client, userdata, message):
        ...
