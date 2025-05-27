# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/17 13:39
# File:web_detect.py
import os
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from config import MQTTConfig
from module import log, DIRECTORY_NAME, ALARM_TIMEOUT
from module.utils import format_time
from module.hook_mqtt import HookMQTTClient
from module.detect import FaceDetect
from module.database import MySQLDatabase
from hardware.sr501 import SR501
from hardware.beep import Beep


class WebFaceDetect(FaceDetect):
    TEMPLATES_FOLDER = os.path.join(DIRECTORY_NAME, 'templates')
    UPLOAD_FOLDER = os.path.join(DIRECTORY_NAME, 'static', 'uploads')

    def __init__(self, database: MySQLDatabase):
        super().__init__(
            database=database,
            cap=None,  # 显式传递None，表示不初始化摄像头
            folder=os.path.join(WebFaceDetect.TEMPLATES_FOLDER, 'static', 'photos')
        )
        self.font = self.load_font()
        self.mqtt = HookMQTTClient(
            ip=MQTTConfig.HOST,
            port=MQTTConfig.PORT,
            topic=MQTTConfig.TOPIC,
            username=MQTTConfig.USERNAME,
            password=MQTTConfig.PASSWORD,
            client_id=MQTTConfig.CLIENT_ID
        )

    @staticmethod
    def load_font():
        try:
            # 尝试加载常见的中文字体。
            font_paths = [
                '/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc',  # 文泉驿正黑。
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Noto字体。
                'simhei.ttf'
            ]

            for font_path in font_paths:
                try:
                    return ImageFont.truetype(font_path, 24)
                except Exception as e:
                    log.error(e)
                    continue
            else:
                log.warning('无法加载中文字体，将使用默认字体。')
                return ImageFont.load_default()  # 所有尝试都失败后使用默认字体。

        except Exception as e:
            log.error(f'字体加载错误,原因:"{e}"')
            return ImageFont.load_default()

    def show_chinese_text(self, img, text, pos, color):
        """支持中文的文本绘制方法"""
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        draw.text(pos, text, font=self.font, fill=color)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def gen_frames(self):
        """生成带有面部检测框和识别结果的视频帧"""
        sr501 = SR501()
        beep = Beep()
        cap = cv2.VideoCapture(0)
        default_frame = (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                cv2.imencode('.jpg', np.zeros((480, 640, 3), dtype=np.uint8))[1].tobytes() +
                b'\r\n'
        )
        # 创建睡眠状态帧（带文字提示）
        sleep_frame_img = np.zeros((480, 640, 3), dtype=np.uint8)
        sleep_frame_img = self.show_chinese_text(
            sleep_frame_img,
            '睡眠中,等待人靠近唤醒...',
            (200, 240),
            (255, 255, 255)
        )
        sleep_frame = (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                cv2.imencode('.jpg', sleep_frame_img)[1].tobytes() +
                b'\r\n'
        )

        if not cap.isOpened():
            log.error('无法访问摄像头!')
            yield default_frame
            return

        try:
            while True:
                while not sr501.detect():
                    log.info('睡眠中,等待人靠近唤醒...')
                    yield sleep_frame
                    time.sleep(1)
                    continue

                log.info('检测到有人靠近,开始识别...')
                start_time = time.time()

                while True:  # 持续识别直到超时或识别成功。
                    success, frame = cap.read()
                    if not success:
                        log.warning('无法读取视频帧!')
                        break

                    faces = self.app.get(frame)  # 面部检测和处理。
                    match_name = None
                    for face in faces:
                        bbox = face.bbox.astype(int)
                        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                        match_name = self.compare_face(face.embedding)
                        recognition_text = f'识别:{match_name}' if match_name else '未识别'
                        text_color = (0, 255, 0) if match_name else (0, 0, 255)

                        frame = self.show_chinese_text(
                            frame,
                            recognition_text,
                            (bbox[0], bbox[3] + 25),
                            text_color
                        )

                    if match_name:
                        _, buffer = cv2.imencode('.jpg', frame)
                        self.mqtt.publish(MQTTConfig.TOPIC, f'[{format_time()}] {match_name}已进入。')
                        yield (
                                b'--frame\r\n'
                                b'Content-Type: image/jpeg\r\n\r\n' +
                                buffer.tobytes() +
                                b'\r\n'
                        )
                        break

                    if (time.time() - start_time) > ALARM_TIMEOUT:
                        frame = self.show_chinese_text(
                            frame,
                            '非法闯入!',
                            (20, 50),
                            (0, 0, 255)
                        )
                        _, buffer = cv2.imencode('.jpg', frame)
                        yield (
                                b'--frame\r\n'
                                b'Content-Type: image/jpeg\r\n\r\n' +
                                buffer.tobytes() +
                                b'\r\n'
                        )
                        log.warning('非法闯入!')
                        self.mqtt.publish(MQTTConfig.TOPIC, f'[{format_time()}] 非法闯入警告!')
                        beep.simple_alarm()
                        break

                    _, buffer = cv2.imencode('.jpg', frame)
                    yield (
                            b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' +
                            buffer.tobytes() +
                            b'\r\n'
                    )

        except Exception as e:
            log.error(f'视频流生成错误,原因:"{e}"')
            yield default_frame
        except KeyboardInterrupt:
            log.info('键盘中断。')
        finally:
            beep.GPIO.clean_up()
            sr501.GPIO.clean_up()
            log.info('GPIO资源释放成功')
            cap.release()
            log.info('摄像头资源释放成功。')
