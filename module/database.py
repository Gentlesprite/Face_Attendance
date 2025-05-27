# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/15 23:22
# File:database.py
import json
import datetime
import mysql.connector
from mysql.connector import Error, DatabaseError
from typing import List, Dict, Any, Optional, Union
from module import log
from module.errors import FaceNotDetected
import numpy as np
import hashlib


class MySQLDatabase:
    NAME = 'name'
    GENDER = 'gender'
    USERNAME = 'username'
    PASSWORD = 'password'
    USER_TYPE = 'user_type'  # 0=普通用户, 1=管理员
    PHOTO_PATH = 'photo_path'
    FACE_META = 'face_meta'
    CREATE_TIME = 'create_time'

    def __init__(
            self,
            host: str,
            database: str,
            user: str,
            password: str
    ):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.connect()
        self._create_table()
        self.data = None
        self.load_data()

    def add(
            self,
            name: str,
            gender: str,
            username: str,
            password: Union[str, int],
            photo_path: str,
            face_meta: Union[np.ndarray, List[float]],
            user_type: int = 0  # 默认为普通用户
    ):
        """添加新用户（用户名自动生成）"""

        # 哈希密码
        hashed_password = self.__hash_password(str(password))

        # 转换为 JSON 字符串
        try:
            face_meta_json = json.dumps(face_meta.tolist() if hasattr(face_meta, 'tolist') else face_meta)
        except Exception as e:
            log.error(e)
            raise FaceNotDetected('转换为json时失败。')

        # 插入数据库
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO users 
                (name, gender, username, password, user_type, photo_path, face_meta, create_time) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (name, gender, username, hashed_password, user_type, photo_path, face_meta_json,
                 datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            self.connection.commit()
            log.info(f'成功添加用户:{name},用户名:{username}。')
            self.load_data()  # 刷新缓存
            return username  # 返回生成的用户名
        except Exception as e:
            self.connection.rollback()
            log.error(f'数据库错误:{e}。')
            raise DatabaseError(f'添加用户失败:{e}')
        finally:
            cursor.close()
            self.load_data()

    def delete(self, username: str) -> bool:
        """根据用户名删除用户"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('DELETE FROM users WHERE username = %s', (username,))
            self.connection.commit()
            affected_rows = cursor.rowcount
            if affected_rows > 0:
                self.load_data()  # 刷新缓存数据
                return True
            return False
        except Error as e:
            log.error(f'删除用户时出错:{e}')
            return False

    def find(self, **kwargs) -> Union[dict, None]:
        """根据条件查找用户"""
        if not kwargs:
            return None

        conditions = []
        values = []
        for key, value in kwargs.items():
            conditions.append(f'{key} = %s')
            values.append(value)

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(f'SELECT * FROM users WHERE {" AND ".join(conditions)} LIMIT 1', tuple(values))
            return cursor.fetchone()

        except Error as e:
            log.error(f'查找用户时出错,原因:"{e}"')
            return None

    def change(self, username: str, **kwargs) -> bool:
        """更新用户信息"""
        if not kwargs:
            return False

        set_clause = []
        values = []
        for key, value in kwargs.items():
            if key == 'face_meta':
                value = json.dumps(value.tolist() if hasattr(value, 'tolist') else value)
            elif key == 'password':
                value = self.__hash_password(value)
            set_clause.append(f'{key} = %s')
            values.append(value)

        values.append(username)  # 添加WHERE条件的值

        try:
            cursor = self.connection.cursor()
            cursor.execute(f'UPDATE users SET {", ".join(set_clause)} WHERE username = %s', tuple(values))
            self.connection.commit()
            affected_rows = cursor.rowcount
            if affected_rows > 0:
                self.load_data()  # 刷新缓存数据
                return True
            return False
        except Error as e:
            log.error(f'更新用户时出错:{e}')
            return False

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
            log.error(f'连接MySQL数据库时出错,原因:"{e}"')
            raise

    def _create_table(self):
        """创建用户表(如果不存在)"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                gender VARCHAR(50) NOT NULL,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                user_type TINYINT DEFAULT 1 NOT NULL,  -- 0=管理员, 1=普通用户
                photo_path VARCHAR(255) NOT NULL,
                face_meta JSON NOT NULL,
                create_time DATETIME NOT NULL
            )
            ''')
            self.connection.commit()
        except Error as e:
            log.error(f'创建表时出错,原因:"{e}"')
            raise

    def load_data(self) -> List[Dict[str, Any]]:
        """从数据库加载所有用户数据"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users')
            result = cursor.fetchall()

            # 将JSON格式的face_meta转换为列表
            for user in result:
                if user.get('face_meta'):
                    user['face_meta'] = json.loads(user['face_meta'])

            self.data = result
            return result
        except Error as e:
            log.error(f'加载数据时出错,原因:"{e}"')
            return []

    @staticmethod
    def __hash_password(password: str) -> str:
        """使用SHA256哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()

    def generate_username(self) -> str:
        """生成自动递增的用户名，格式为年月日+ID（如2024051601）"""
        today = datetime.datetime.now().strftime('%Y%m%d')
        cursor = self.connection.cursor()

        try:
            # 查找今天最大的ID
            cursor.execute(
                "SELECT MAX(CAST(SUBSTRING(username, 9) AS UNSIGNED)) as max_id "
                "FROM users WHERE username LIKE %s",
                (f"{today}%",)
            )
            result = cursor.fetchone()
            max_id = result[0] if result[0] is not None else 0

            # 生成新ID
            new_id = max_id + 1
            return f"{today}{new_id:02d}"  # 格式化为两位数，如01, 02等
        except Error as e:
            log.error(f'生成用户名时出错,原因:"{e}"')
            raise
        finally:
            cursor.close()

    def authenticate(self, username: str, password: str) -> bool:
        """验证用户凭据"""
        user = self.find(username=username)
        if not user:
            return False
        hashed_input = self.__hash_password(password)
        return user.get('password') == hashed_input

    def is_admin(self, username: str) -> bool:
        """检查用户是否为管理员"""
        user = self.find(username=username)
        return user and user.get('user_type', 1) == 0

    def close(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            log.info('MySQL连接已关闭。')

    def __del__(self):
        try:
            self.close()
        except (Exception, ModuleNotFoundError):
            pass
