# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/5/16 21:48
# File:app.py
import os
import datetime

import pandas as pd
from io import BytesIO
from flask import send_file
from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.datastructures.file_storage import FileStorage
from flask import Flask, render_template, Response, request, url_for, redirect

from module.database import JsonDatabase
from module.web_detect import WebFaceDetect

app = Flask(__name__)


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
        # 获取表单数据
        name = request.form.get('name')
        age = int(request.form.get('age'))
        gender = request.form.get('gender')
        uid = int(request.form.get('uid'))

        # 处理文件上传
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

            web_detector.add_face(
                name=name,
                age=age,
                gender=gender,
                uid=uid,
                photo_path=photo_path
            )
            return redirect(url_for('index'))

    # GET请求返回表单页面
    return render_template('add_face.html')


@app.route('/workers', methods=['GET'])
def workers():
    for record in jd.data:
        if 'create_time' in record:
            record['formatted_time'] = datetime.datetime.fromtimestamp(record['create_time']).strftime(
                '%Y-%m-%d %H:%M:%S')

    if request.args.get('export') == 'excel':
        df = pd.DataFrame(jd.data)

        if JsonDatabase.CREATE_TIME in df.columns:
            df[JsonDatabase.CREATE_TIME] = pd.to_datetime(df[JsonDatabase.CREATE_TIME], unit='s')

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

    return render_template('workers.html', records=jd.data)


if __name__ == '__main__':
    # 初始化数据库和检测器
    jd = JsonDatabase('database.json')
    web_detector = WebFaceDetect(jd)
    os.makedirs(WebFaceDetect.UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = WebFaceDetect.UPLOAD_FOLDER

    app.run(host='0.0.0.0', port=5000, debug=True)
