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
        self._cached_users = self._preprocess_data()

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
            self.jd.load_data()
        return face_meta

    def _preprocess_data(self):
        users = []
        for user in self.jd.data:
            face_meta = user.get(self.jd.FACE_META)
            if face_meta:
                # 转换为numpy数组并归一化
                meta_array = np.array(face_meta, dtype=np.float32)
                norm = np.linalg.norm(meta_array)
                if norm == 0:
                    continue  # 跳过无效特征
                meta_normalized = meta_array / norm
                users.append({
                    'name': user[self.jd.NAME],
                    'uid': user.get(self.jd.UID),
                    'meta': meta_normalized
                })
        return users

    def compare_face(self, unknown_face_meta, tolerance=0.32, min_confidence=0.6):
        try:
            if not self._cached_users:
                return None

            # 归一化未知特征
            unknown_meta = np.array(unknown_face_meta, dtype=np.float32)
            norm = np.linalg.norm(unknown_meta)
            if norm == 0:
                return None  # 无效输入
            unknown_meta_normalized = unknown_meta / norm

            # 批量提取已知特征
            known_metas = [user['meta'] for user in self._cached_users]
            distances = face_recognition.face_distance(known_metas, unknown_meta_normalized)

            # 找到最佳匹配
            min_index = np.argmin(distances)
            best_distance = distances[min_index]
            best_user = self._cached_users[min_index]

            # 计算置信度并检查阈值
            confidence = 1 - best_distance
            if best_distance <= tolerance and confidence >= min_confidence:
                return best_user['name']
            return None

        except Exception as _:
            # 实际应用中应记录日志
            del _
            return None

    def detect_face(self):

        face_meta = self.__get_face_meta(detect=True)
        if face_meta is None:
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
                    self._cached_users = self._preprocess_data()
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
