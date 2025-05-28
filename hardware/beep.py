# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/22 22:23
# File:beep.py
import time

from module import log
from hardware import BEEP_PIN, import_error


class Beep:
    def __init__(self):
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.GPIO.setwarnings(False)
            self.GPIO.setmode(GPIO.BCM)
            self.GPIO.setup(BEEP_PIN, GPIO.OUT, initial=GPIO.HIGH)  # 初始高电平（静音）
        except ImportError as e:
            import_error(e)

    def beep_on(self):
        """开启蜂鸣器（低电平触发）"""
        self.GPIO.output(BEEP_PIN, self.GPIO.LOW)

    def beep_off(self):
        """关闭蜂鸣器（高电平静音）"""
        self.GPIO.output(BEEP_PIN, self.GPIO.HIGH)

    def simple_alarm(self, duration=5):
        """简单急促警报（哔-哔-哔）"""
        log.debug('启动简单急促警报。')
        start_time = time.time()
        while time.time() - start_time < duration:
            self.beep_on()  # 发声
            time.sleep(0.1)
            self.beep_off()  # 静音
            time.sleep(0.1)
        self.beep_off()  # 确保最后静音

    def rising_alarm(self, duration=5):
        """频率渐升警报（音调逐渐升高）"""
        log.debug('启动频率渐升警报。')
        start_time = time.time()
        while time.time() - start_time < duration:
            for beep_duration in [0.05, 0.03, 0.01]:  # 越短越急促
                self.beep_on()
                time.sleep(beep_duration)
                self.beep_off()
                time.sleep(0.02)
        self.beep_off()

    def pulse_alarm(self, duration=5):
        """脉冲式警报（强弱变化）"""
        log.debug('启动脉冲式警报。')
        start_time = time.time()
        while time.time() - start_time < duration:
            # 模拟强弱变化
            for _ in range(3):
                self.beep_on()
                time.sleep(0.05)
                self.beep_off()
                time.sleep(0.05)
            time.sleep(0.2)
        self.beep_off()

    def police_siren(self, duration=5):
        """警笛式警报（类似警车鸣笛）"""
        log.debug('启动警笛式警报。')
        start_time = time.time()
        while time.time() - start_time < duration:
            # 模拟警笛音调变化
            for _ in range(2):
                self.beep_on()
                time.sleep(0.1)
                self.beep_off()
                time.sleep(0.1)
            time.sleep(0.2)
        self.beep_off()

    def beep_pattern(self, duration=5):
        """节奏型警报（三短一长）"""
        log.debug('启动节奏型警报。')
        start_time = time.time()
        while time.time() - start_time < duration:
            # 三短
            for _ in range(3):
                self.beep_on()
                time.sleep(0.1)
                self.beep_off()
                time.sleep(0.1)
            # 一长
            self.beep_on()
            time.sleep(0.5)
            self.beep_off()
            time.sleep(0.2)
        self.beep_off()


class PWMBeep:
    def __init__(self):
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.GPIO.setwarnings(False)
            self.GPIO.setmode(GPIO.BCM)
            self.GPIO.setup(BEEP_PIN, GPIO.OUT)
            self.pwm = GPIO.PWM(BEEP_PIN, 1000)
            self.pwm.start(0)  # 初始占空比为0，不发声
        except ImportError as e:
            import_error(e)

    def simple_alarm(self, duration=5):
        """简单急促警报"""
        log.debug('启动简单急促警报。')
        self.pwm.ChangeDutyCycle(50)  # 设置占空比为50%
        start_time = time.time()
        while time.time() - start_time < duration:
            self.pwm.ChangeFrequency(2000)
            time.sleep(0.1)
            self.pwm.ChangeFrequency(1000)
            time.sleep(0.1)
        self.pwm.ChangeDutyCycle(0)

    def rising_alarm(self, duration=5):
        """频率渐升警报"""
        log.debug('启动频率渐升警报。')
        self.pwm.ChangeDutyCycle(50)
        start_time = time.time()
        while time.time() - start_time < duration:
            for freq in range(1000, 3000, 50):
                self.pwm.ChangeFrequency(freq)
                time.sleep(0.02)
        self.pwm.ChangeDutyCycle(0)

    def pulse_alarm(self, duration=5):
        """脉冲式警报"""
        log.debug('启动脉冲式警报。')
        start_time = time.time()
        while time.time() - start_time < duration:
            for dc in range(0, 101, 5):
                self.pwm.ChangeDutyCycle(dc)
                self.pwm.ChangeFrequency(1500)
                time.sleep(0.01)
            for dc in range(100, -1, -5):
                self.pwm.ChangeDutyCycle(dc)
                self.pwm.ChangeFrequency(1500)
                time.sleep(0.01)
        self.pwm.ChangeDutyCycle(0)

    def police_siren(self, duration=5):
        """警笛式警报"""
        log.debug('启动警笛式警报。')
        self.pwm.ChangeDutyCycle(50)
        start_time = time.time()
        while time.time() - start_time < duration:
            # 快速上升
            for freq in range(800, 1800, 20):
                self.pwm.ChangeFrequency(freq)
                time.sleep(0.01)
            # 快速下降
            for freq in range(1800, 800, -20):
                self.pwm.ChangeFrequency(freq)
                time.sleep(0.01)
        self.pwm.ChangeDutyCycle(0)

    def beep_pattern(self, duration=5):
        """节奏型警报"""
        log.debug('启动节奏型警报。')
        self.pwm.ChangeDutyCycle(50)
        start_time = time.time()
        while time.time() - start_time < duration:
            # 三短一长
            for _ in range(3):
                self.pwm.ChangeFrequency(2000)
                time.sleep(0.1)
                self.pwm.ChangeFrequency(0)  # 通过频率设为0实现静音
                time.sleep(0.1)
            self.pwm.ChangeFrequency(1500)
            time.sleep(0.5)
            self.pwm.ChangeFrequency(0)
            time.sleep(0.2)
        self.pwm.ChangeDutyCycle(0)


if __name__ == '__main__':
    from module import console

    beep = None
    while True:
        console.print(
            '===选择蜂鸣器的驱动方式===\n1.PWM驱动\n2.电平驱动')
        choice = console.input('请选择驱动模式(1-2):')
        if choice == '1':
            beep = PWMBeep()
            break
        elif choice == '2':
            beep = Beep()
            console.print(f'"{choice}"无效选择,请重试。')
            break
        else:
            continue
    try:
        console.print(
            '===门禁系统报警测试===\n1.简单急促警报\n2.频率渐升警报\n3.脉冲式警报\n4.警笛式警报\n5.节奏型警报')
        while True:
            choice = console.input('请选择报警模式(1-5):')
            if choice == '1':
                beep.simple_alarm()
            elif choice == '2':
                beep.rising_alarm()
            elif choice == '3':
                beep.pulse_alarm()
            elif choice == '4':
                beep.police_siren()
            elif choice == '5':
                beep.beep_pattern()
            else:
                console.print(f'"{choice}"无效选择,请重试。')
                continue
            break
    except KeyboardInterrupt:
        pass
    finally:
        beep.GPIO.cleanup()
