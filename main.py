# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:17
# File:main.py
import os

from module.database import JsonDatabase
from module.detect import FaceDetect

if __name__ == '__main__':
    jd = JsonDatabase(os.path.join(os.getcwd(), 'database.json'))
    fd = FaceDetect(jd)
    fd.add_face(name='卢治宇', age='18', gender='男', uid=1)  # 新增人脸测试。

    # fd.detect_loop(detect=True) # 检测人脸
