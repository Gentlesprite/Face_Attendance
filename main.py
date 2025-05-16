# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:17
# File:main.py
import os

from module import console
from module.database import JsonDatabase
from module.detect import FaceDetect

jd = JsonDatabase(os.path.join(os.getcwd(), 'database.json'))
fd = FaceDetect(jd)


def detect_face():
    face_meta = fd.get_face_meta(detect=True)
    if face_meta is None:
        console.print('未检测到人脸，请重试')
        return

    known_faces = jd.find()
    match_name = fd.recognize_face(face_meta, known_faces)
    if match_name:
        console.print(f'识别结果: 欢迎回来, {match_name}!')
    else:
        console.print('未识别到注册用户')


def add_face():
    name = input('名字:')
    age = int(input('年龄:'))
    gender = input('性别:')
    uid = int(input('uid:'))

    while True:
        face_meta = fd.get_face_meta(name, age, gender, uid)
        if face_meta is not None:
            break
        console.print('未检测到人脸,请重试...')

    console.print('\n=== 人脸识别 ===\n请面对摄像头进行识别...')
    detect_face()


detect_face()
