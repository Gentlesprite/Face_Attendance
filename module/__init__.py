# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:15
# File:__init__.py
import os
import logging
from rich.console import Console
from rich.logging import RichHandler
from logging.handlers import RotatingFileHandler

__version__ = '1.0.1'
LOG_TIME_FORMAT = '[%Y-%m-%d %H:%M:%S]'
console = Console(log_path=False, log_time_format=LOG_TIME_FORMAT)
SOFTWARE_SHORT_NAME = 'FRS'
APPDATA_PATH = os.path.join(
    os.environ.get('APPDATA') or os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config')),
    SOFTWARE_SHORT_NAME)
LOG_PATH = os.path.join(APPDATA_PATH, f'{SOFTWARE_SHORT_NAME}_LOG.log')
os.makedirs(APPDATA_PATH, exist_ok=True)
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 0  # 不保留日志文件
# 配置日志文件处理器（支持日志轮换）
file_handler = RotatingFileHandler(
    filename=LOG_PATH,
    maxBytes=MAX_LOG_SIZE,
    backupCount=BACKUP_COUNT,
    encoding='UTF-8'
)
file_handler.setFormatter(logging.Formatter('%(message)s'))
# 配置日志记录器
logging.basicConfig(
    level=logging.WARNING,
    format='%(message)s',
    datefmt=LOG_TIME_FORMAT,
    handlers=[
        RichHandler(rich_tracebacks=True,
                    console=console,  # v1.2.5传入控制台对象,修复报错时进度条打印错位
                    show_path=False,
                    omit_repeated_times=False,
                    log_time_format=LOG_TIME_FORMAT),
        file_handler  # 文件输出
    ]
)
log = logging.getLogger('rich')
