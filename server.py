from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
import os
import random

import tensorflow as tf

with tf.device('/cpu:0'):

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.getcwd(), 'gumikedatabase.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origines='*')

class Comments(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scene = db.Column(db.String(10))
    timecode = db.Column(db.Integer)
    comment = db.Column(db.String(40))
    
    def __init__(self, scene, timecode, comment):
        self.scene = scene
        self.timecode = timecode
        self.comment = comment

class TotalHearts(db.Model):
    __tablename__ = 'total_hearts'
    
    total_hearts = db.Column(db.Integer, primary_key=True)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('connected')
    
@socketio.on('disconnect')
def handle_disconnect():
    print('disconnected')
    
# for add new comment
@socketio.on('comment')
def handle_comment(data):
    comment = data['comment']
    timecode = int(data['timecode'])
    scene = data['scene']
    new_comment = Comments(scene=scene, timecode=timecode, comment=comment)
    db.session.add(new_comment)
    db.session.commit()
    #全プレイヤーに通知、送信
    socketio.emit('new_comment', comment)
    
# for get comment
@app.route('/get_comments/<scene>', methods=['GET'])
def get_comments(scene):
    datas = Comments.query.filter_by(scene=scene).all()
    comments = []
    for data in datas:
        comments.append({"comment": data.comment})
    if len(comments) == 0:
        return jsonify([])
    print(datas)
    return jsonify(comments)


@app.route('/add', methods=['GET', 'POST'])
def add_total_hearts():
    total_hearts = TotalHearts.query.first()
    if not total_hearts:
        total_hearts = TotalHearts(total_hearts=0)
    total_hearts.total_hearts += 1
    db.session.commit()
    return 'add total hearts!'

if __name__ == '__main__':
    app = Flask(__name__)
    socketio.run(app, debug=True,port=8000)
    app.debug = True
    http_server = WSGIServer(('', 8000), app, handler_class=WebSocketHandler)
    http_server.serve_forever()

from flask import request
from flask_restful import Resource

class AddComment(Resource):
    def post(self):
        comment = request.json['comment']
        timecode = int(request.json['timecode'])
        scene = request.json['scene']
        new_comment = Comments(scene=scene, timecode=timecode, comment=comment)
        db.session.add(new_comment)
        db.session.commit()
        return {'message': 'Comment added successfully.'}
