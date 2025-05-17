# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/17 13:39
# File:web.py
import os

import cv2
import numpy as np
import face_recognition

from PIL import Image, ImageDraw, ImageFont

from module import log, DIRECTORY_NAME
from module.detect import FaceDetect
from module.database import JsonDatabase


class WebFaceDetect(FaceDetect):
    TEMPLATES_FOLDER = os.path.join(DIRECTORY_NAME, 'templates')
    UPLOAD_FOLDER = os.path.join(DIRECTORY_NAME, 'static', 'uploads')

    def __init__(self, database: JsonDatabase):
        super().__init__(
            database=database,
            cap=None,
            folder=os.path.join(WebFaceDetect.TEMPLATES_FOLDER, 'static', 'photos')
        )
        # 加载中文字体
        try:
            self.font = ImageFont.truetype('simhei.ttf', 24)
        except Exception as e:
            log.error(e)
            # 如果找不到字体，使用默认字体（可能不支持中文）
            self.font = ImageFont.load_default()

    def show_chinese_text(self, img, text, pos, color):
        """支持中文的文本绘制方法"""
        # 将OpenCV图像转换为PIL图像
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        # 绘制中文文本
        draw.text(pos, text, font=self.font, fill=color)
        # 转换回OpenCV格式
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def gen_frames(self):
        """生成带有面部检测框和识别结果的视频帧"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            log.error('无法访问摄像头!')

        try:
            while True:
                success, frame = cap.read()
                if not success:
                    break

                # 转换为RGB格式用于face_recognition
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # 检测人脸位置
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                # 在检测到的人脸周围画框并显示识别结果
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    # 绘制人脸框
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

                    # 识别人脸
                    match_name = self.compare_face(face_encoding)

                    if match_name:
                        # 使用支持中文的方法显示识别出的名字
                        text = f'识别: {match_name}'
                        frame = self.show_chinese_text(frame, text, (left, bottom + 25), (0, 255, 0))
                    else:
                        # 显示未识别
                        text = '未识别'
                        frame = self.show_chinese_text(frame, text, (left, bottom + 25), (0, 0, 255))

                # 将帧转换为JPEG格式
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        finally:
            cap.release()
