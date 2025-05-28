# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/21 16:51
# File:dhtxx.py
import time
import threading

from hardware import DHTxx_PIN, import_error
from module import log


class DHTxx:
    II: str = '11'
    ZZ: str = '22'

    def __init__(self, hardware: str = '11'):
        self.temperature = 25
        self.humidity = 50
        try:
            import adafruit_dht
            if hardware == DHTxx.II:
                self.dht = adafruit_dht.DHT11(DHTxx_PIN, use_pulseio=False)
            elif hardware == DHTxx.ZZ:
                self.dht = adafruit_dht.DHT22(DHTxx_PIN, use_pulseio=False)
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
    from module import console

    device = None
    while True:
        console.print('===选择温湿度模块===\n1.DHT11\n2.DHT22')
        choice = console.input('请选择温湿度模块(1-2):')
        if choice == '1':
            device = DHTxx.II
            break
        elif choice == '2':
            device = DHTxx.ZZ
            break
        else:
            console.print(f'"{choice}"无效选择,请重试。')
            continue
    dht = DHTxx(hardware=device)

    while True:
        try:
            console.print(dht.get_data())
            time.sleep(1)
        except KeyboardInterrupt:
            dht.dht.exit()
