# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:22
# File:database.py
import json
import datetime
import mysql.connector
from mysql.connector import Error, DatabaseError
from typing import List, Dict, Any, Optional
from module import log
from module.errors import UserAlreadyExists


class MySQLDatabase:
    NAME = 'name'
    AGE = 'age'
    GENDER = 'gender'
    UID = 'uid'
    PHOTO_PATH = 'photo_path'
    FACE_META = 'face_meta'
    CREATE_TIME = 'create_time'

    def __init__(self, host: str, database: str, user: str, password: str):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.connect()
        self._create_table()
        self.data = None
        self.load_data()

    def connect(self):
        """连接到MySQL数据库"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            if self.connection.is_connected():
                log.info('成功连接到MySQL数据库。')
        except Error as e:
            log.error(f"连接MySQL数据库时出错: {e}")
            raise

    def _create_table(self):
        """创建用户表（如果不存在）"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            age INT NOT NULL,
            gender VARCHAR(50) NOT NULL,
            uid INT UNIQUE NOT NULL,
            photo_path VARCHAR(255) NOT NULL,
            face_meta JSON NOT NULL,
            create_time DATETIME NOT NULL
        )
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(create_table_query)
            self.connection.commit()
        except Error as e:
            log.error(f"创建表时出错: {e}")
            raise

    def load_data(self) -> List[Dict[str, Any]]:
        """从数据库加载所有用户数据"""
        query = "SELECT * FROM users"
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            result = cursor.fetchall()

            # 将JSON格式的face_meta转换为列表
            for user in result:
                if user.get('face_meta'):
                    user['face_meta'] = json.loads(user['face_meta'])

            self.data = result
        except Error as e:
            log.error(f"加载数据时出错: {e}")
            return []

    def add(self, name: str, age: int, gender: str, uid: int, photo_path: str, face_meta):
        """添加新用户"""

        # 检查用户是否已存在（如果 find() 方法也涉及 face_meta 判断，同样要修改）
        if self.find(uid=uid):
            raise UserAlreadyExists(f"UID为{uid}的用户已存在")

        # 转换为 JSON 字符串（确保 face_meta 是 NumPy 数组或 List[float]）
        try:
            face_meta_json = json.dumps(face_meta.tolist() if hasattr(face_meta, 'tolist') else face_meta)
        except Exception as e:
            log.error(e)
        # 插入数据库
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, age, gender, uid, photo_path, face_meta, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (name, age, gender, uid, photo_path, face_meta_json,
                 datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            self.connection.commit()
            log.info(f"成功添加用户: {name}")
            self.load_data()  # 刷新缓存
        except Exception as e:
            self.connection.rollback()
            log.error(f"数据库错误: {e}")
            raise DatabaseError(f"添加用户失败: {e}")
        finally:
            cursor.close()
            self.load_data()
    def delete(self, uid: int) -> bool:
        """根据UID删除用户"""
        delete_query = "DELETE FROM users WHERE uid = %s"
        try:
            cursor = self.connection.cursor()
            cursor.execute(delete_query, (uid,))
            self.connection.commit()
            affected_rows = cursor.rowcount
            if affected_rows > 0:
                self.load_data()  # 刷新缓存数据
                return True
            return False
        except Error as e:
            log.error(f"删除用户时出错: {e}")
            return False

    def find(self, **kwargs) -> Optional[Dict[str, Any]]:
        """根据条件查找用户"""
        if not kwargs:
            return None

        conditions = []
        values = []
        for key, value in kwargs.items():
            conditions.append(f"{key} = %s")
            values.append(value)

        query = f"SELECT * FROM users WHERE {' AND '.join(conditions)} LIMIT 1"
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, tuple(values))
            result = cursor.fetchone()
            if result and 'face_meta' in result:
                result['face_meta'] = json.loads(result['face_meta'])
            return result
        except Error as e:
            log.error(f"查找用户时出错: {e}")
            return None

    def update(self, uid: int, **kwargs) -> bool:
        """更新用户信息"""
        if not kwargs:
            return False

        set_clause = []
        values = []
        for key, value in kwargs.items():
            if key == 'face_meta':
                value = json.dumps(value.tolist() if hasattr(value, 'tolist') else value)
            set_clause.append(f"{key} = %s")
            values.append(value)

        values.append(uid)  # 添加WHERE条件的值

        query = f"UPDATE users SET {', '.join(set_clause)} WHERE uid = %s"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(values))
            self.connection.commit()
            affected_rows = cursor.rowcount
            if affected_rows > 0:
                self.load_data()  # 刷新缓存数据
                return True
            return False
        except Error as e:
            log.error(f"更新用户时出错: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            log.info('MySQL连接已关闭。')

    def __del__(self):
        self.close()
