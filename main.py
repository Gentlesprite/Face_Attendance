# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:17
# File:main.py
import cv2

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
    fd = FaceDetect(db, cap=cv2.VideoCapture(0))
    while True:
        result = fd.detect_face(fd.take_photo())
        exit(0) if result else None
