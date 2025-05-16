# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:57
# File:face.py
import os
import cv2
import datetime
from typing import Union

import face_recognition

from module import log


class FaceDetect:
    def __init__(self, database, cap=cv2.VideoCapture(0), folder: str = 'photos'):
        self.cap = cap
        self.folder: str = folder
        self.jd = database

    def __take_photo(self) -> Union[str, None]:
        ret, frame = self.cap.read()
        if not ret:
            log.error('无法访问摄像头。')
            return None
        os.makedirs(self.folder, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        photo_path = f'{self.folder}/{timestamp}.jpg'
        cv2.imwrite(photo_path, frame)
        return photo_path

    def get_face_meta(self, name=None, age=None, gender=None, uid=None, detect=False):
        photo_path = self.__take_photo()
        if photo_path is None:
            return None

        photo = face_recognition.load_image_file(photo_path)
        face = face_recognition.face_locations(photo)

        if not face:
            log.warning('未检测到人脸!')
            return None  # 不再递归调用，由调用方决定是否重试

        face_meta = face_recognition.face_encodings(photo, face)[0]

        if not detect:
            self.jd.add(
                name=name,
                age=age,
                gender=gender,
                uid=uid,
                face_path=photo_path,
                face_meta=face_meta
            )
        return face_meta

    @staticmethod
    def recognize_face(unknown_face_meta, known_face_meta):

        for name, meta in known_face_meta:
            # 比较人脸特征
            results = face_recognition.compare_faces([meta], unknown_face_meta)
            if results[0]:
                return name

        return None
