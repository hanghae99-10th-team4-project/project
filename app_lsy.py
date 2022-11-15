from pymongo import MongoClient
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

import certifi

ca = certifi.where()
client = MongoClient('mongodb+srv://jwchoi:jwchoi@cluster0.etdnidi.mongodb.net/?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.sparta

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/index_lsy')
def home_lsy():
    return render_template('index_lsy.html')

@app.route("/api/walk", methods=["GET"]) #walk doc 가져오기
def review_get():
    review_give = list(db.walk.find({},{'_id':False}))
    comment_give = list(db.walk_comment.find({},{'_id':False}))

    return jsonify({'review': review_give}, {'comment': comment_give})

@app.route("/api/walk/comment", methods=["POST"]) #코멘트 저장하기
def comment_post():
    post_id_receive = request.form['post_id']
    user_id_receive = request.form['user_id']
    comment_receive = request.form['comment_give']
    star_receive = request.form['star']

    comment_list = list(db.walk_comment.find({},{'_id': False}))
    count = len(comment_list) + 1

    doc = {
        'post_id' :post_id_receive,
        'user_id' : user_id_receive,
        'comment_id' : count,
        'comment' : comment_receive,
        'star': star_receive
    }

    db.walk_comment.insert_one(doc)

    return jsonify({'msg': '등록완료'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
