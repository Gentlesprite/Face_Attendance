# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:57
# File:face.py
import datetime
import os
from typing import Union

import cv2
import face_recognition

import module.database
from module import log, console
from module.errors import UserAlreadyExists


class FaceDetect:
    def __init__(self, database: module.database.JsonDatabase, cap=cv2.VideoCapture(0), folder: str = 'photos'):
        self.cap = cap
        self.folder: str = folder
        self.jd = database

    def __take_photo(self) -> Union[str, None]:
        ret, frame = self.cap.read()
        if not ret:
            log.error('无法访问摄像头!')
            return None
        # 转换为灰度图像（减少计算量）
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 直方图均衡化（增强对比度）
        gray = cv2.equalizeHist(gray)

        # 转换为RGB格式（face_recognition需要）
        rgb_frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

        os.makedirs(self.folder, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        photo_path = f'{self.folder}/{timestamp}.jpg'
        cv2.imwrite(photo_path, rgb_frame)
        return photo_path

    def __get_face_meta(
            self, name: Union[str, None] = None,
            age: Union[int, None] = None,
            gender: Union[str, None] = None,
            uid: Union[int, None] = None,
            detect: bool = False
    ):
        photo_path = self.__take_photo()
        if photo_path is None:
            return None

        photo = face_recognition.load_image_file(photo_path)
        face = face_recognition.face_locations(photo)

        if not face:
            log.warning('未检测到人脸!')
            return None

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
                face_path=photo_path,
                face_meta=face_meta
            )
        return face_meta

    def compare_face(self, unknown_face_meta, tolerance=0.5) -> Union[str, None]:
        known_face_meta = self.jd.find()
        try:
            for name, meta in known_face_meta:
                # 比较人脸特征，降低tolerance值提高严格度
                results = face_recognition.compare_faces([meta], unknown_face_meta, tolerance=tolerance)
                if results[0]:
                    # 添加距离检查
                    face_distance = face_recognition.face_distance([meta], unknown_face_meta)[0]
                    if face_distance < tolerance:
                        return name
            return None
        except (IndexError, TypeError):
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

    def detect_loop(self, *args, **kwargs):
        while True:
            try:
                face_meta = self.__get_face_meta(
                    name=kwargs.get('name'),
                    age=kwargs.get('age'),
                    gender=kwargs.get('gender'),
                    uid=kwargs.get('uid'),
                    detect=kwargs.get('detect', False)
                )
                if face_meta is None:
                    console.print('未检测到人脸,请重试...')
                match_name: Union[None, str] = self.compare_face(face_meta)
                if match_name:
                    console.log(f'欢迎回来,识别结果:{match_name}!')
                    return match_name
            except UserAlreadyExists as e:
                log.warning(e)
                return None

    def add_face(self):
        name = console.input('名字:')
        age = int(console.input('年龄:'))
        gender = console.input('性别:')
        uid = int(console.input('uid:'))
        self.detect_loop(name, age, gender, uid)

        console.print('\n=== 人脸识别 ===\n请面对摄像头进行识别...')
        self.detect_face()
