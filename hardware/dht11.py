# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/21 16:51
# File:dht11.py
from typing import Union
from module import log


class DHTxx:
    def __init__(self):
        self.temperature = None
        self.humidity = None
        try:
            import adafruit_dht
            import board
            self.dht = adafruit_dht.DHT11(board.D26)
        except ImportError as e:
            log.warning(f'当前运行环境并非树莓派,无法使用硬件,原因:"{e}"')

    def get_environment_data(self) -> Union[dict, None]:
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
