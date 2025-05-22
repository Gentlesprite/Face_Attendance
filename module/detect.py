# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:57
# File:face.py
import os
import numpy as np
from typing import List, Dict, Any, Union
import cv2
from insightface.app import FaceAnalysis
from insightface.app.common import Face
from module import log, console
from module.utils import process_image
from module.database import MySQLDatabase


class FaceDetect:
    def __init__(self, database: MySQLDatabase, cap=None, folder: str = 'photos'):
        self.cap = cap  # 不在这里初始化摄像头
        self.folder: str = folder
        self.db = database
        # 初始化InsightFace应用
        self.app = FaceAnalysis(
            name='antelopev2',
            root='./models',
            allowed_modules=['detection', 'recognition'],
            providers=['CPUExecutionProvider']
        )
        # 使用更小的检测尺寸
        self.app.prepare(ctx_id=0, det_size=(160, 160), det_thresh=0.3)
        self.__cached_users = self.__pre_process_data()

    def take_photo(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        # 缩小图像尺寸
        frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        return process_image(frame, self.folder)

    def __get_face_meta(
            self,
            photo_path: str = None
    ) -> dict:

        if photo_path is None:
            return {
                'face': None,
                'photo_path': None,
                'e_code': '调用摄像头失败或没有图片'
            }

        cv2_photo = cv2.imread(photo_path)
        if cv2_photo is None:
            return {
                'face': None,
                'photo_path': None,
                'e_code': f'无法读取图片'
            }

        faces = self.app.get(cv2_photo, max_num=1)

        try:
            face: Face = faces[0]  # 取第一个检测到的人脸。
            return {
                'face': face,
                'photo_path': photo_path,
                'e_code': None
            }
        except (IndexError, Exception):
            os.remove(photo_path)
            return {
                'face': None,
                'photo_path': None,
                'e_code': '未检测到人脸'
            }

    def __pre_process_data(self) -> List[Dict[str, Any]]:
        users = []
        for user in self.db.data:
            face_meta = user.get(self.db.FACE_META)
            if face_meta:
                # 转换为numpy数组并归一化。
                meta_array = np.array(face_meta, dtype=np.float32)
                norm = np.linalg.norm(meta_array)
                if norm == 0:
                    continue  # 跳过无效特征
                meta_normalized = meta_array / norm
                users.append({
                    'name': user[self.db.NAME],
                    'username': user.get(self.db.USERNAME),
                    'meta': meta_normalized
                })
        return users

    def compare_face(
            self,
            unknown_face_meta: np.ndarray,
            tolerance: float = 0.6,
            min_confidence: float = 0.6
    ):
        try:
            if not self.__cached_users:
                return None

            # 归一化未知特征
            unknown_meta = np.array(unknown_face_meta, dtype=np.float32)
            norm = np.linalg.norm(unknown_meta)
            if norm == 0:
                return None  # 无效输入
            unknown_meta_normalized = unknown_meta / norm

            # 批量提取已知特征
            known_metas = [user['meta'] for user in self.__cached_users]

            # 计算余弦相似度
            similarities = []
            for known_meta in known_metas:
                similarity = np.dot(unknown_meta_normalized, known_meta)
                similarities.append(similarity)

            similarities = np.array(similarities)

            # 找到最佳匹配
            max_index = np.argmax(similarities)
            best_similarity = similarities[max_index]
            best_user = self.__cached_users[max_index]

            # 检查阈值
            if best_similarity >= tolerance and best_similarity >= min_confidence:
                return best_user['name']
            return None

        except Exception as e:
            log.error(f'人脸比对出错:{e}')
            return None

    def detect_face(self, photo_path) -> Union[str, None]:
        meta = self.__get_face_meta(photo_path)
        face = meta.get('face')
        if face is None:
            return None

        match_name = self.compare_face(face.embedding)
        if match_name:
            console.log(f'识别结果:欢迎回来,{match_name}!')
            return match_name
        else:
            console.log('未识别到注册用户!')
            return None

    def add_face(
            self,
            name: str,
            gender: str,
            password: Union[str, int],
            user_type: Union[int, str] = None,
            photo_path: Union[str, None] = None
    ) -> dict:
        user_type: int = 1 if user_type is None else 0
        photo_path: str = self.take_photo() if not photo_path else process_image(photo_path, self.folder)
        meta: dict = self.__get_face_meta(photo_path)
        face: Union[Face, None] = meta.get('face')
        if face and self.compare_face(face.embedding):
            face = None
            meta['e_code'] = '面部信息已存在'
        if face:
            username = self.db.generate_username()
            self.db.add(
                name=name,
                gender=gender,
                username=username,
                password=password,
                user_type=user_type,
                photo_path=photo_path,
                face_meta=face.embedding.tolist()
            )
            console.print(f'新增用户:{name},用户名:{username}。')
            self.__cached_users = self.__pre_process_data()
        return {
            'e_code': meta.get('e_code')
        }
