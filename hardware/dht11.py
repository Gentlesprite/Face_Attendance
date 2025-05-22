# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/21 16:51
# File:dht11.py
import threading
import time

from hardware import DHTxx_PIN, import_error
from module import log, console


class DHTxx:
    def __init__(self):
        self.temperature = 25  # 默认值
        self.humidity = 50
        try:
            import adafruit_dht
            self.dht = adafruit_dht.DHT11(DHTxx_PIN, use_pulseio=False)
        except RuntimeError as e:
            log.warning(f'温湿度传感器初始化失败,原因"{e}"')
        except ImportError as e:
            import_error(e)

    def get_data(self) -> dict:
        try:
            self.temperature = self.dht.temperature
            self.humidity = self.dht.humidity
        except RuntimeError as e:
            log.warning(f'温度读取失败,原因"{e}"')
        except Exception as e:
            log.error(f'调用温湿度传感器时发生了错误,原因:"{e}"')
        finally:
            return {
                'temperature': self.temperature,
                'humidity': self.humidity
            }

    def loop(self):
        def _loop():
            while True:
                self.get_data()
                log.info(f'温度:{self.temperature} 湿度:{self.humidity}')
                time.sleep(1)

        threading.Thread(target=_loop).start()


if __name__ == '__main__':
    dht11 = DHTxx()
    while True:
        try:
            console.print(dht11.get_data())
            time.sleep(1)
        except KeyboardInterrupt:
            pass
