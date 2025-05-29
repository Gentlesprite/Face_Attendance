# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/22 22:28
# File:__init__.py
from module import log


def import_error(_e):
    log.warning(f'当前运行环境并非树莓派,无法使用硬件,原因:"{_e}"')


try:
    import board
except ImportError as e:
    import_error(e)
DHTxx_PIN = board.D26
BEEP_PIN: int = 16
SR501_PIN: int = 14
RGB_PIN: tuple = (1, 7, 8)
