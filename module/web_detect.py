# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/17 13:39
# File:web.py
import os

import cv2
import numpy as np

from PIL import Image, ImageDraw, ImageFont

from module import log, DIRECTORY_NAME
from module.detect import FaceDetect
from module.database import MySQLDatabase


class WebFaceDetect(FaceDetect):
    TEMPLATES_FOLDER = os.path.join(DIRECTORY_NAME, 'templates')
    UPLOAD_FOLDER = os.path.join(DIRECTORY_NAME, 'static', 'uploads')

    def __init__(self, database: MySQLDatabase):
        super().__init__(
            database=database,
            cap=None,  # 显式传递None，表示不初始化摄像头
            folder=os.path.join(WebFaceDetect.TEMPLATES_FOLDER, 'static', 'photos')
        )
        try:
            self.font = ImageFont.truetype('simhei.ttf', 24)
        except Exception as e:
            log.error(e)
            self.font = ImageFont.load_default()

    def show_chinese_text(self, img, text, pos, color):
        """支持中文的文本绘制方法"""
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        draw.text(pos, text, font=self.font, fill=color)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def gen_frames(self):
        """生成带有面部检测框和识别结果的视频帧"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            log.error('无法访问摄像头!')
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   cv2.imencode('.jpg', np.zeros((480, 640, 3), dtype=np.uint8))[1].tobytes() +
                   b'\r\n')
            return

        try:
            while True:
                success, frame = cap.read()
                if not success:
                    break

                # 使用InsightFace进行人脸检测
                faces = self.app.get(frame)

                # 在检测到的人脸周围画框并显示识别结果
                for face in faces:
                    # 绘制人脸框
                    bbox = face.bbox.astype(int)
                    cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)

                    # 识别人脸
                    match_name = self.compare_face(face.embedding)

                    if match_name:
                        # 使用支持中文的方法显示识别出的名字
                        text = f'识别: {match_name}'
                        frame = self.show_chinese_text(frame, text, (bbox[0], bbox[3] + 25), (0, 255, 0))
                    else:
                        # 显示未识别
                        text = '未识别'
                        frame = self.show_chinese_text(frame, text, (bbox[0], bbox[3] + 25), (0, 0, 255))

                # 将帧转换为JPEG格式
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        finally:
            cap.release()