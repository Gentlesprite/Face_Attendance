# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/16 20:06
# File:utils.py
import os
import datetime
import cv2


def process_image(path, folder) -> str:
    # 转换为灰度图像（减少计算量）
    photo = path if isinstance(path, cv2.typing.MatLike) else cv2.imread(path)
    os.makedirs(folder, exist_ok=True)
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    # 直方图均衡化（增强对比度）
    gray = cv2.equalizeHist(gray)
    # 转换为RGB格式（face_recognition需要）
    rgb_frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    photo_path = f'{folder}/{timestamp}.jpg'
    cv2.imwrite(photo_path, rgb_frame)
    return photo_path
