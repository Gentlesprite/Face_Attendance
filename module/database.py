# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:22
# File:database.py
import os
import json
import datetime
import numpy as np


class JsonDatabase:
    NAME = 'name'
    AGE = 'age'
    GENDER = 'gender'
    UID = 'uid'
    FACE_PATH = 'face_path'
    FACE_META = 'face_meta'
    CREATE_TIME = 'create_time'

    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump([], f)

    def add(self, name: str, age: int, gender: str, uid: int, face_path, face_meta):
        with open(self.path, 'r+') as f:
            meta = json.load(f)
            if face_meta is not None:
                face_meta = face_meta.tolist()
            new_worker = {
                JsonDatabase.NAME: name,
                JsonDatabase.AGE: age,
                JsonDatabase.GENDER: gender,
                JsonDatabase.UID: uid,
                JsonDatabase.FACE_PATH: face_path,
                JsonDatabase.FACE_META: face_meta,
                JsonDatabase.CREATE_TIME: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            meta.append(new_worker)  # 修正这里，应该是追加到meta而不是face_meta
            f.seek(0)
            json.dump(meta, f, indent=2)

    def delete(self, name):
        ...

    def find(self):
        if not os.path.exists(self.path):
            raise []
        with open(self.path, 'r') as f:
            meta = json.load(f)
            return [(person.get(JsonDatabase.NAME), np.array(person.get(JsonDatabase.FACE_META)))
                    for person in meta if person.get(JsonDatabase.FACE_META) is not None]

    def change(self):
        ...
