# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:22
# File:database.py
import os
import json
import datetime


class JsonDatabase:
    NAME = 'name'
    AGE = 'age'
    GENDER = 'gender'
    UID = 'uid'
    PHOTO_PATH = 'photo_path'
    FACE_META = 'face_meta'
    CREATE_TIME = 'create_time'

    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump([], f)
        with open(self.path, 'r') as f:
            self.data: dict = json.load(f)

    def add(self, name: str, age: int, gender: str, uid: int, photo_path, face_meta):
        with open(self.path, 'r+') as f:
            meta = json.load(f)
            if face_meta is not None:
                face_meta = face_meta.tolist()
            new_worker = {
                JsonDatabase.NAME: name,
                JsonDatabase.AGE: age,
                JsonDatabase.GENDER: gender,
                JsonDatabase.UID: uid,
                JsonDatabase.PHOTO_PATH: photo_path,
                JsonDatabase.FACE_META: face_meta,
                JsonDatabase.CREATE_TIME: datetime.datetime.now().timestamp()
            }
            meta.append(new_worker)
            f.seek(0)
            json.dump(meta, f, indent=2)

    def delete(self, name):
        ...

    def find(self, *args):
        for i in args:
            for j in self.data:
                return j.get(i)

    def change(self):
        ...
