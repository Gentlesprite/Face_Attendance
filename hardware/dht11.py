# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/21 16:51
# File:dht11.py
from typing import Union
from module import log


def get_environment_data() -> Union[dict, None]:
    temperature = None
    humidity = None
    try:
        import adafruit_dht
        import board
        import time
        dht = adafruit_dht.DHT11(board.D26)
        temperature = dht.temperature
        humidity = dht.humidity
    except ImportError as e:
        log.warning(f'当前运行环境并非树莓派,无法使用硬件,原因:"{e}"')
    except RuntimeError as e:
        log.warning(f'温度读取失败,原因"{e}"')
    except Exception as e:
        log.error(f'调用温湿度传感器时发生了错误,原因:"{e}"')
    finally:
        return {
            'temperature': temperature,
            'humidity': humidity
        }
