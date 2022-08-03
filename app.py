from flask import Flask, render_template, jsonify, request, redirect, url_for
import json
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from pymongo import MongoClient
from flask_cors import CORS
import jwt
import hashlib

client = MongoClient('localhost', 27017)
db = client.modutrip

app = Flask(__name__)
CORS(app, resources={r'*': {'origins': '*'}})

SECRET_KEY = 'SPARTA'

# @app.route('/')
# def home():
#     return render_template('mypage.html')
#################################
## HTML을 주는 부분 ##
#################################
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('main.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


# 로그인 페이지
@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,
        "password": password_hash,
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    # print(value_receive, type_receive, exists)
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/api/mypage', methods=['GET'])
def show_diary():
    diaries = list(db.diary.find({}, {'_id': False}))
    return jsonify({'all_diary': diaries})

@app.route('/api/mypage', methods=['POST'])
def save_diary():
    title_receive = request.form['title_give']
    content_receive = request.form['content_give']

    file = request.files["file_give"]
    extension = file.filename.split('.')[-1]
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
    filename = f'file-{mytime}'
    save_to = f'static/upload/{filename}.{extension}'
    file.save(save_to)
    doc = {
        'title': title_receive,
        'content': content_receive,
        'file': f'{filename}.{extension}',
        'time': today.strftime('%Y.%m.%d')
    }
    db.diary.insert_one(doc)
    return jsonify({'result': 'success', 'msg': '게시물이 업로드 되었습니다.'})

@app.route('/listing', methods=['GET'])
def listing():
    diarys = list(db.diary.find({},{'_id':False}))
    print("diary = ", end=""), print(diarys)
    return jsonify({'diarys':diarys})

@app.route('/article')
def article():
    return render_template('article.html')
#
@app.route('/api/article', methods=['GET'])
def list_article():
    diarys = list(db.diary.find({},{'_id':False}))
    return jsonify({'diarys': diarys})

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/mypage')
def mypage():
    return render_template('mypage.html')
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
