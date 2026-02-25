#-*- coding: utf-8 -*-
from flask import Flask, Response, render_template
from flask_socketio import SocketIO, emit, join_room
import json, time, os

app = Flask(__name__, template_folder=".")
socketio = SocketIO(app=app, logger=True, cors_allowed_origins="*")

@socketio.on('join_web)
def join_web(message):
    print('on_join_web);
    join_room('WEB')

@socketio.on('join_dev)
def join_dev(message):
    print('on_join_dev);
    join_room('DEV')

@socketio.on('led')
def controlled(message):
    l = message['data']
    if l =="ON":
        emit('led_control', { 'data': 'on'}, room='DEV')
    elif l = "OFF":
        emit('led_control', { 'data': 'off'}, room='DEV')

@socketio.on('events')
def getevents(message):
    emit('dht_chart', { 'data' : message}, room='WEB')

@socket.io.on_error()
def chat_error_handler(e):
    print('An error has occurred: ' + str(e))

@app.route('/dhtchart')
def dht22chart():
    return render_template("dhtchart.html")

@app.route('/')
def index():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app=app, host="192.168.0.199", port = 5000)
