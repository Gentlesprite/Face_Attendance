# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/29 16:24
# File:led_140c05.py
import re

from module import log
from hardware import RGB_PIN, import_error


class Color(dict):
    RED = (0, 100, 100)
    GREEN = (100, 100, 0)
    BLUE = (100, 0, 100)
    YELLOW = (0, 100, 0)
    PURPLE = (0, 0, 100)
    CYAN = (100, 0, 0)
    WHITE = ON = (0, 0, 0)
    BLACK = OFF = (100, 100, 100)

    def __init__(self):
        # 将类属性同步到字典
        for name, value in self.__class__.__dict__.items():
            if not name.startswith('_') and not callable(value):
                self[name] = value
        super().__init__()


class LED140C05:
    def __init__(
            self,
            red_pin=RGB_PIN[0],
            green_pin=RGB_PIN[1],
            blue_pin=RGB_PIN[2]
    ):
        try:
            import RPi.GPIO as GPIO
            self.R = red_pin
            self.G = green_pin
            self.B = blue_pin
            self.GPIO = GPIO
            self.GPIO.setmode(GPIO.BCM)
            self.GPIO.setup(self.R, GPIO.OUT)
            self.GPIO.setup(self.G, GPIO.OUT)
            self.GPIO.setup(self.B, GPIO.OUT)
            # 初始状态为关闭(共阳极：高电平=灭)
            self.GPIO.output(self.R, GPIO.HIGH)
            self.GPIO.output(self.G, GPIO.HIGH)
            self.GPIO.output(self.B, GPIO.HIGH)
            self.color: dict = Color()
        except ImportError as e:
            import_error(e)

    def set_color(self, color_name):
        color = color_name.upper()

        if color in self.color:
            self.__set_rgb(*self.color[color])
            return True
        elif color.startswith('#'):
            log.warning('十六进制颜色码需要PWM支持,当前模式仅支持基本颜色。')
            return False
        else:
            log.warning(f'未知颜色:"{color_name}"。')
            return False

    def __set_rgb(self, r, g, b):
        """直接设置RGB电平（共阳极：0=开，1=关）"""
        self.GPIO.output(self.R, self.GPIO.HIGH if r else self.GPIO.LOW)
        self.GPIO.output(self.G, self.GPIO.HIGH if g else self.GPIO.LOW)
        self.GPIO.output(self.B, self.GPIO.HIGH if b else self.GPIO.LOW)

    def cleanup(self):
        """清理GPIO资源"""
        self.GPIO.cleanup()


class PWMLED140C05(LED140C05):
    def __init__(
            self,
            red_pin=RGB_PIN[0],
            green_pin=RGB_PIN[1],
            blue_pin=RGB_PIN[2],
            frequency=70
    ):
        super().__init__(red_pin, green_pin, blue_pin)

        try:
            self.pwm_R = self.GPIO.PWM(self.R, frequency)
            self.pwm_G = self.GPIO.PWM(self.G, frequency)
            self.pwm_B = self.GPIO.PWM(self.B, frequency)
            self.pwm_R.start(100)
            self.pwm_G.start(100)
            self.pwm_B.start(100)
        except ImportError as e:
            import_error(e)

    def set_color(self, color_name):
        color = color_name.upper()

        if color in self.color:
            # 使用PWM设置基础颜色
            r, g, b = self.color[color]
            self.__set_rgb_pwm(
                0 if not r else 100,
                0 if not g else 100,
                0 if not b else 100
            )
            return True
        elif color.startswith('#'):
            return self.__set_hex_color(color_name.strip().lstrip('#'))
        else:
            log.warning(f'未知颜色:"{color_name}"。')
            return False

    def __set_hex_color(self, hex_color):
        """通过十六进制颜色码设置LED颜色（如 '#FF0000' 表示红色）"""
        # 移除 # 并检查格式
        hex_color = hex_color.strip().lstrip('#')
        if not re.match(r'^[0-9A-Fa-f]{6}$', hex_color):
            log.error('错误的格式,颜色格式应为#RRGGBB - 如:"#FF0000"。')
            return False

        # 解析为RGB分量(0-255)
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # 转换为PWM占空比(0-100，共阳极：0=全亮，100=全灭)
        r_pwm = 100 - int((r / 255) * 100)
        g_pwm = 100 - int((g / 255) * 100)
        b_pwm = 100 - int((b / 255) * 100)

        self.__set_rgb_pwm(r_pwm, g_pwm, b_pwm)
        return True

    def __set_rgb_pwm(self, r, g, b):
        """直接设置RGB占空比（0-100，共阳极：0=全亮，100=全灭）"""
        self.pwm_R.ChangeDutyCycle(r)
        self.pwm_G.ChangeDutyCycle(g)
        self.pwm_B.ChangeDutyCycle(b)

    def cleanup(self):
        """清理GPIO资源"""
        self.pwm_R.stop()
        self.pwm_G.stop()
        self.pwm_B.stop()
        super().cleanup()


if __name__ == '__main__':
    from module import console

    led = None
    prompt = ''
    while True:
        console.print(
            '===选择LED灯的驱动方式===\n1.PWM驱动\n2.电平驱动')
        choice = console.input('请选择驱动模式(1-2):')
        if choice == '1':
            led = PWMLED140C05()
            prompt = '===RGB灯测试===(输入颜色名称(如:"red")或十六进制码 - 如:"#FF0000"。)'
            break
        elif choice == '2':
            led = LED140C05()
            prompt = '===RGB灯测试===(输入颜色名称如:"red", "green", "blue", "yellow"等)'
            console.print(f'"{choice}"无效选择,请重试。')
            break
        else:
            continue

    try:
        while True:
            console.print(prompt)
            choice = console.input('请选择需要点亮的颜色:')
            if choice.lower() in ('exit', 'q'):
                break

            led.set_color(choice)

    except KeyboardInterrupt:
        pass
    finally:
        led.cleanup()
