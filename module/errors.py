# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/16 11:59
# File:error.py
class FaceAttendanceError(Exception):
    """所有自定义异常的基类"""
    pass


class UserAlreadyExists(FaceAttendanceError):
    def __init__(self, message: str = None):
        super().__init__(message)
        self.username = message


class FaceNotDetected(FaceAttendanceError):
    def __init__(self, message: str):
        super().__init__(message)
