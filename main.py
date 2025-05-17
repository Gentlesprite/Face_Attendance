# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:17
# File:main.py
import os

from module.database import MySQLDatabase
from module.detect import FaceDetect

if __name__ == '__main__':
    MYSQL_CONFIG = {
        'host': 'localhost',
        'database': 'face_attendance',
        'user': 'root',
        'password': '123'
    }
    db = MySQLDatabase(**MYSQL_CONFIG)
    fd = FaceDetect(db)
    while True:
        if fd.detect_face():  # 检测人脸
            break
