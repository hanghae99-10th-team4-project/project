from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

from pymongo import MongoClient
import certifi

ca = certifi.where()
client = MongoClient('mongodb+srv://test:sparta@cluster0.9vezsln.mongodb.net/?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.dbsparta

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮습니다.
# 이 문자열은 서버만 알고있기 때문에, 내 서버에서만 토큰을 인코딩(=만들기)/디코딩(=풀기) 할 수 있습니다.
SECRET_KEY = 'SPARTA'
# JWT 패키지를 사용합니다. (설치해야할 패키지 이름: PyJWT)
import jwt
# 토큰에 만료시간을 줘야하기 때문에, datetime 모듈도 사용합니다.
import datetime
# 회원가입 시엔, 비밀번호를 암호화하여 DB에 저장해두는 게 좋습니다.
# 그렇지 않으면, 개발자(=나)가 회원들의 비밀번호를 볼 수 있으니까요.^^;
import hashlib


#################################
##  HTML을 주는 부분             ##
#################################
@app.route('/')
def go_api():
    return redirect('/api')

@app.route('/api')

def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.member.find_one({"user_id": payload['id']})
        return render_template('index.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
@app.route('/api/member')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/api/main')
def main():
    return render_template('index.html')

@app.route('/signup')
def register():
    return render_template('signup.html')


#################################
##  로그인을 위한 API            ##
#################################

# [회원가입 API]
# id, pw, nickname을 받아서, mongoDB에 저장합니다.
# 저장하기 전에, pw를 sha256 방법(=단방향 암호화. 풀어볼 수 없음)으로 암호화해서 저장합니다.
@app.route('/api/member/signup', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.member.insert_one({'user_id': id_receive, 'passwd': pw_hash})

    return jsonify({'result': 'success'})

@app.route('/api/member/signup/checkid', methods=['POST'])
def check_id():
    id_receive = request.form['id_give']

    check_user = db.member.find_one({'user_id':id_receive})
    if check_user is not None:
        return jsonify({'check_user': 'fail'})
    else :
        return jsonify({'check_user': 'success'})


# [로그인 API]
# id, pw를 받아서 맞춰보고, 토큰을 만들어 발급합니다.
@app.route('/api/member', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
    result = db.member.find_one({'user_id': id_receive, 'passwd': pw_hash})

    # 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
        # JWT 토큰에는, payload와 시크릿키가 필요합니다.
        # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
        # 아래에선 id와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저ID 값을 알 수 있습니다.
        # exp에는 만료시간을 넣어줍니다. 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        # token을 줍니다.
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

@app.route('/review_page')
def home_review_page():
    return render_template('review_page.html')

@app.route("/api/walk", methods=["GET"]) #walk db 가져오기
def review_get():
    review_give = list(db.walk.find({},{'_id':False}))

    return jsonify({'review': review_give})

@app.route("/api/walk/comment", methods=["GET"]) #comment db 가져오기
def comment_get():
    comment_give = list(db.walk_comment.find({}, {'_id': False}))
    return jsonify({'comments': comment_give})

@app.route("/api/walk/comment", methods=["POST"]) #코멘트 저장하기
def comment_post():
    post_id_receive = request.form['post_id']
    comment_receive = request.form['comment_give']
    star_receive = request.form['star']

    comment_list = list(db.walk_comment.find({},{'_id': False}))
    count = len(comment_list) + 1

    token_receive = request.cookies.get('mytoken')

    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.member.find_one({"user_id": payload['id']})
    user_id_receive = user_info['user_id']

    doc = {
        'post_id': post_id_receive,
        'user_id': user_id_receive,
        'comment_id': count,
        'comment': comment_receive,
        'star': star_receive
    }

    db.walk_comment.insert_one(doc)
    return jsonify({'msg': '등록완료'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
