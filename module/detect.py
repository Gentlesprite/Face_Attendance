# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:57
# File:face.py
import os
import numpy as np
from typing import Union, List, Dict, Any
import cv2
from insightface.app import FaceAnalysis
from module import log, console
from module.utils import process_image
from module.database import MySQLDatabase
from module.errors import UserAlreadyExists


class FaceDetect:
    def __init__(self, database: MySQLDatabase, cap=None, folder: str = 'photos'):
        self.cap = cap  # 不在这里初始化摄像头
        self.folder: str = folder
        self.db = database

        # 初始化InsightFace应用
        self.app = FaceAnalysis(
            name='antelopev2',
            root='./models',
            allowed_modules=['detection', 'recognition', 'genderage'],
            providers=['CPUExecutionProvider']
        )
        # 使用更小的检测尺寸
        self.app.prepare(ctx_id=-1, det_size=(320, 320))  # ctx_id=-1表示强制使用CPU
        self._cached_users = self._preprocess_data()

    def __take_photo(self):
        ret, frame = self.cap.read()
        if not ret: return None
        # 缩小图像尺寸
        frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        return process_image(frame, self.folder)

    def __get_face_meta(
            self, name: Union[str, None] = None,
            age: Union[int, None] = None,
            gender: Union[str, None] = None,
            uid: Union[int, None] = None,
            photo_path: Union[str, None] = None,
            detect: bool = False  # 为True时只方法将只充当检测功能。
    ) -> Union[Dict[str, Any], None]:

        photo_path = self.__take_photo() if not photo_path else photo_path
        if photo_path is None:
            return None

        # 使用InsightFace进行人脸检测和特征提取
        img = cv2.imread(photo_path)
        if img is None:
            log.error(f'无法读取图片: {photo_path}')
            return None

        faces = self.app.get(img, max_num=1)

        if not faces:
            log.warning('未检测到人脸!')
            os.remove(photo_path)
            return None

        if detect:
            os.remove(photo_path)

        # 取第一个检测到的人脸
        face = faces[0]

        # 构建返回的元数据
        face_meta = {
            'embedding': face.embedding,  # 人脸特征向量
            'bbox': face.bbox,  # 人脸框坐标
            'landmark': face.landmark,  # 人脸关键点
            'det_score': face.det_score,  # 检测分数
            'gender': face.gender,  # 预测性别
            'age': face.age  # 预测年龄
        }

        if not detect:
            match_name = self.compare_face(face.embedding)
            if match_name:
                raise UserAlreadyExists(f'用户"{match_name}"已注册,请勿重复添加。')
            try:
                self.db.add(
                    name=name,
                    age=age if age is not None else face.age,
                    gender=gender if gender is not None else ('男' if face.gender == 1 else '女'),
                    uid=uid,
                    photo_path=photo_path,
                    face_meta=face.embedding.tolist()  # 转换为列表存储
                )
            except Exception as e:
                raise e
        return face_meta

    def _preprocess_data(self) -> List[Dict[str, Any]]:
        users = []
        for user in self.db.data:
            face_meta = user.get(self.db.FACE_META)
            if face_meta:
                # 转换为numpy数组并归一化
                meta_array = np.array(face_meta, dtype=np.float32)
                norm = np.linalg.norm(meta_array)
                if norm == 0:
                    continue  # 跳过无效特征
                meta_normalized = meta_array / norm
                users.append({
                    'name': user[self.db.NAME],
                    'uid': user.get(self.db.UID),
                    'meta': meta_normalized
                })
        return users

    def compare_face(self, unknown_face_meta: np.ndarray, tolerance: float = 0.6, min_confidence: float = 0.6) -> Union[
        str, None]:
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

            # 计算余弦相似度
            similarities = []
            for known_meta in known_metas:
                similarity = np.dot(unknown_meta_normalized, known_meta)
                similarities.append(similarity)

            similarities = np.array(similarities)

            # 找到最佳匹配
            max_index = np.argmax(similarities)
            best_similarity = similarities[max_index]
            best_user = self._cached_users[max_index]

            # 检查阈值
            if best_similarity >= tolerance and best_similarity >= min_confidence:
                return best_user['name']
            return None

        except Exception as e:
            log.error(f'人脸比对出错: {e}')
            return None

    def detect_face(self) -> Union[str, None]:
        face_meta = self.__get_face_meta(detect=True)
        if face_meta is None:
            return None

        match_name = self.compare_face(face_meta['embedding'])
        if match_name:
            console.log(f'识别结果:欢迎回来, {match_name}!')
            return match_name
        else:
            console.log('未识别到注册用户!')
            return None

    def add_face(self, **kwargs) -> None:
        try:
            name = kwargs.get('name') or console.input('名字:')
            age = kwargs.get('age')
            if age is None:
                age_input = console.input('年龄(留空使用自动检测):')
                age = int(age_input) if age_input else None
            gender = kwargs.get('gender')
            if gender is None:
                gender = console.input('性别(留空使用自动检测):')
            uid = kwargs.get('uid')
            if uid is None:
                uid = int(console.input('uid:'))
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
                            continue

                        match_name = self.compare_face(face_meta['embedding'])
                        if match_name:
                            console.log(f'欢迎回来,识别结果:{match_name}!')
                            break
                    except UserAlreadyExists as e:
                        log.warning(e)
                        break
                self.detect_face()
        except Exception as e:
            log.exception(e)
