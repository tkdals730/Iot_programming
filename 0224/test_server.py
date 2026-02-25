from flask import Flask, request

app = Flask(__name__)

@app.route('/ping')
def ping():
    print("접속자 IP:", request.remote_addr)
    return "pong"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 5000, debug = True)