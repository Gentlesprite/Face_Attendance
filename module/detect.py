# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:57
# File:face.py
import os
import numpy as np
from typing import Union

import cv2
import face_recognition

from module import log, console
from module.utils import process_image
from module.database import JsonDatabase
from module.errors import UserAlreadyExists


class FaceDetect:
    def __init__(self, database: JsonDatabase, cap=cv2.VideoCapture(0), folder: str = 'photos'):
        self.cap = cap
        self.folder: str = folder
        self.jd = database

    def __take_photo(self) -> Union[str, None]:
        ret, frame = self.cap.read()
        if not ret:
            log.error('无法访问摄像头!')
            return None

        return process_image(frame, self.folder)

    def __get_face_meta(
            self, name: Union[str, None] = None,
            age: Union[int, None] = None,
            gender: Union[str, None] = None,
            uid: Union[int, None] = None,
            photo_path: Union[str, None] = None,
            detect: bool = False  # 为True时只方法将只充当检测功能。
    ):
        photo_path = self.__take_photo() if not photo_path else photo_path
        if photo_path is None:
            return None

        photo = face_recognition.load_image_file(photo_path)
        face = face_recognition.face_locations(photo)

        if not face:
            log.warning('未检测到人脸!')
            os.remove(photo_path)
            return None
        if detect:
            os.remove(photo_path)

        face_meta = face_recognition.face_encodings(photo, face)[0]

        if not detect:
            match_name = self.compare_face(face_meta)
            if match_name:
                raise UserAlreadyExists(f'用户"{match_name}"已注册,请勿重复添加。')
            self.jd.add(
                name=name,
                age=age,
                gender=gender,
                uid=uid,
                photo_path=photo_path,
                face_meta=face_meta
            )
        return face_meta

    def compare_face(self, unknown_face_meta, tolerance=0.4, min_confidence=0.6):
        try:
            data = {}
            for user in self.jd.data:
                if user.get(self.jd.FACE_META):
                    data[user[self.jd.NAME]] = {
                        'meta': np.array(user[self.jd.FACE_META]),
                        'uid': user.get(self.jd.UID)
                    }

            if not data:
                return None

            best_match = None
            best_distance = 1.0  # 初始设为最大距离

            for name, user_data in data.items():
                distance = face_recognition.face_distance(
                    [user_data['meta']],
                    unknown_face_meta
                )[0]

                if distance < best_distance and distance < tolerance:
                    best_distance = distance
                    best_match = (name, user_data['uid'], distance)

            # 添加置信度检查
            if best_match and (1 - best_distance) >= min_confidence:
                return best_match[0]  # 返回匹配的用户名
            return None

        except Exception as _:
            del _
            return None

    def detect_face(self):

        face_meta = self.__get_face_meta(detect=True)
        if face_meta is None:
            log.warning('未检测到人脸,请重试。')
            return

        match_name = self.compare_face(face_meta)
        if match_name:
            console.log(f'识别结果:欢迎回来, {match_name}!')
            return match_name
        else:
            console.log('未识别到注册用户!')
            return None

    def add_face(
            self,
            **kwargs
    ):
        try:
            name = kwargs.get('name') or console.input('名字:')
            age = int(kwargs.get('age') or console.input('年龄:'))
            gender = kwargs.get('gender') or console.input('性别:')
            uid = int(kwargs.get('uid') or console.input('uid:'))
            photo_path = kwargs.get('photo_path')
            if photo_path:
                face_meta = self.__get_face_meta(
                    name=name,
                    age=age,
                    gender=gender,
                    uid=uid,
                    detect=False,
                    photo_path=process_image(photo_path, self.folder)
                )
                if face_meta is None:
                    console.print('在照片中未检测到人脸,请重试...')
                else:
                    console.print(f'新增用户:{name}。')
            else:
                detect = True if len(kwargs) == 1 else False
                while True:
                    try:
                        face_meta = self.__get_face_meta(
                            name=name,
                            age=age,
                            gender=gender,
                            uid=uid,
                            detect=detect
                        )
                        if face_meta is None:
                            console.print('未检测到人脸,请重试...')
                        match_name: Union[None, str] = self.compare_face(face_meta)
                        if match_name:
                            console.log(f'欢迎回来,识别结果:{match_name}!')
                            break
                    except UserAlreadyExists as e:
                        log.warning(e)
                        break
                self.detect_face()
        except Exception as e:
            log.error(e)
