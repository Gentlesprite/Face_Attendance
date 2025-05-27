# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/27 12:31
# File:mqtt.py
import paho.mqtt.client as mqtt

from module import log


class MQTTClient:
    def __init__(
            self,
            ip: str,
            port: int,
            topic: str,
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
        self.__connect()
        self.client.loop_forever() if main_loop else self.client.loop_start()

    def __config_callback(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def __connect(self):
        try:
            if self.client.connect(self.ip, self.port, 60) == 0:
                log.info('连接MQTT服务器成功。')
                self.client.subscribe(self.topic)
                log.info(
                    f'"{self.client_id}"新增订阅主题:{",".join(self.topic) if isinstance(self.topic, list) else self.topic}。')
            else:
                raise ConnectionError('Failed to connect to MQTT server.')

        except (Exception, ConnectionError) as e:
            log.error(f'连接MQTT服务器失败,请检查配置文件或服务器状态,原因:"{e}"')

    @staticmethod
    def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            log.error(f'连接MQTT服务器失败,错误码:"{reason_code}"')

    @staticmethod
    def on_message(client, userdata, message):
        log.info(f'收到消息 - [Topic]:{message.topic} [Message]:{message.payload.decode()}')

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> None:
        """
        发布消息到指定的MQTT主题

        :param topic: 要发布消息的主题
        :param payload: 要发布的消息内容
        :param qos: 服务质量等级 (0, 1, 或 2)
        :param retain: 是否保留消息
        """
        result = self.client.publish(topic, payload, qos, retain)
        if result.rc == 0:
            log.info(f'消息发布成功 - [Topic]:{topic} [Message]:{payload}')
        else:
            log.error(f'消息发布失败 - [Topic]:{topic} [Error]:{mqtt.error_string(result.rc)}')


if __name__ == '__main__':
    from module import console

    try:
        console.print('===测试MQTT服务器===\n1.测试其他客户端接收消息\n2.测试本地客户端发送消息')
        _main_loop = False
        while True:
            choice = console.input('请选择测试项目(1-2):')
            if choice == '1':
                _main_loop = True
                console.print('请使用其他客户端设置订阅主题"test"并发送消息,查看终端是否这正常接收。')
                break
            elif choice == '2':
                _main_loop = False
                console.print(
                    '请先使用其他客户端订阅主题"pi"并等待消息发布,若无响应,请先将其他客户端订阅主题"pi"后,重新运行当前程序。')
                break
            else:
                console.print(f'"{choice}"无效选择。')
                continue
        mqtt = MQTTClient(
            ip=console.input('输入MQTT服务器IP:'),
            port=1883,
            topic='test',
            username='admin',
            password='public',
            client_id='pi-lzy',
            main_loop=_main_loop
        )
        mqtt.publish('pi', 'This is a test message.') if not _main_loop else None
    except KeyboardInterrupt:
        pass
