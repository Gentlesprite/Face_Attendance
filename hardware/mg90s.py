# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/29 21:36
# File:mg90s.py

import time
import board
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685

from module import log


class ServoController:
    def __init__(self, channel=0, frequency=50, closed_angle=0, open_angle=135):
        self.i2c = board.I2C()
        self.pca = PCA9685(self.i2c)
        self.pca.frequency = frequency
        self.servo = servo.Servo(self.pca.channels[channel])
        self.closed_angle = closed_angle
        self.open_angle = open_angle

    def open_door(self, wait_time=3):
        """打开门并保持指定时间后关闭"""
        try:
            self.servo.angle = self.open_angle
            log.debug('门已开。')
            time.sleep(wait_time)
            self.servo.angle = self.closed_angle
            log.debug('门已关。')
            time.sleep(2)
        except Exception as e:
            log.error(f'操作伺服电机时出错,原因:"{e}"')

    def clean_up(self):
        self.pca.deinit()


# 使用示例
if __name__ == '__main__':
    servo_ctrl = ServoController(channel=0)

    try:
        servo_ctrl.open_door()

    finally:
        servo_ctrl.clean_up()
