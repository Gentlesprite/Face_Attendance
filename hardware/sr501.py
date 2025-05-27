# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/24 18:49
# File:sr501.py
import time
from hardware import SR501_PIN, import_error


class SR501:
    def __init__(self):
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.GPIO.setmode(GPIO.BCM)
            self.GPIO.setup(SR501_PIN, GPIO.IN)
        except ImportError as e:
            import_error(e)

    def detect(self) -> bool:
        try:
            return bool(self.GPIO.input(SR501_PIN))
        except RuntimeError:
            return False


if __name__ == '__main__':
    from module import console

    sr501 = SR501()
    try:
        while True:
            console.print(sr501.detect())
            time.sleep(1)
    except (Exception, KeyboardInterrupt, RuntimeError):
        sr501.GPIO.cleanup()
