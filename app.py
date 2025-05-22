# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/16 21:48
# File:app.py
import os
from io import BytesIO
from functools import wraps

import pandas as pd
from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.datastructures.file_storage import FileStorage
from flask import Flask, render_template, Response, redirect, send_file, jsonify, url_for, request, session

from module import log
from module.database import MySQLDatabase
from module.web_detect import WebFaceDetect
from hardware.dht11 import DHTxx

app = Flask(__name__)
app.secret_key = '1234-5678'


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_meta: dict = db.find(username=username)
        if db.authenticate(username, password):
            session['username'] = username
            if user_meta.get('user_type') == 0:
                session['is_admin'] = True
            else:
                log.warning(f'{username}权限不足。')
            return redirect(url_for('workers'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video')
def video():
    return Response(
        web_detector.gen_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/add_face', methods=['GET', 'POST'])
def add_face():
    # 配置文件上传

    if request.method == 'POST':
        # 获取表单数据。
        name = request.form.get('name')
        gender = request.form.get('gender')
        password = str(request.form.get('password'))

        # 处理文件上传。
        if 'photo' not in request.files:
            return redirect(request.url)
        file: ImmutableMultiDict = request.files
        photo: FileStorage = file.get('photo')
        file_name: str = photo.filename
        if not file_name:
            return redirect(request.url)

        if photo and '.' in file_name and file_name.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}:
            photo_path = os.path.join(app.config.get('UPLOAD_FOLDER'), secure_filename(file_name))
            photo.save(photo_path)

            meta = web_detector.add_face(
                name=name,
                gender=gender,
                password=password,
                photo_path=photo_path
            )
            e_code = meta.get('e_code')
            if e_code:
                msg = f'添加失败,原因:"{e_code}"'
                log.error(msg)
                return jsonify({'status': 'error', 'message': msg})
            else:
                msg = f'"{name}"添加成功。'
                log.info(msg)
                return jsonify({'status': 'success', 'message': msg})
    return render_template('add_face.html')


@app.route('/workers', methods=['GET'])
@admin_required
def workers():
    if request.args.get('export') == 'excel':
        df = pd.DataFrame(db.data)
        df.pop('photo_path')
        df.pop('face_meta')

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='员工列表', index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='output.xlsx'
        )

    return render_template('workers.html', records=db.data)


@app.route('/dht11')
def get_sensor_data():
    return jsonify(dht11.get_environment_data())


if __name__ == '__main__':
    try:
        from config import HOST, PORT, MYSQL_CONFIG
    except ImportError:
        with open('config.py', 'w') as f:
            '''
            # coding=UTF-8
            # Author:Gentlesprite
            # File:config.py
            HOST: str = '0.0.0.0'
            PORT: int = 5000
            MYSQL_CONFIG = {
                'host': ...,
                'database': ...,
                'user': ...,
                'password': ...
            }
            '''
        log.warning('请先完善"config.py"配置文件。')
        exit(0)
    db = MySQLDatabase(**MYSQL_CONFIG)
    web_detector = WebFaceDetect(db)
    os.makedirs(WebFaceDetect.UPLOAD_FOLDER, exist_ok=True)
    dht11 = DHTxx()
    #dht11.event_loop()
    app.config['UPLOAD_FOLDER'] = WebFaceDetect.UPLOAD_FOLDER
    app.run(host='0.0.0.0', port=5000, debug=True)
