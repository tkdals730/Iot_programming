from flask import Flask,render_template, jsonify, request
from datetime import datetime
import serial
import time
import pymysql
import mysql.connector
import threading 

app = Flask(__name__)

# ── MySQL 연결 ──────────────────────────────

def get_connection():

    return mysql.connector.connect(

        host="localhost",

        user="root",

        password="test1234",

        database="sensor_db"

    )

# ── Arduino 데이터 읽기 ─────────────────────

def read_sensor():
    """Arduino에서 센서 데이터 1개를 읽어 딕셔너리로 반환"""
    try:
        ser = serial.Serial("COM4", 9600, timeout=2)
        time.sleep(2)
        line = ser.readline().decode("utf-8").strip()
        ser.close()
        parts = line.split(",")
        return {
            "humidity": float(parts[0]),
            "temperature":    float(parts[1])
        }
    except Exception as e:
        print("센서 오류:", e)
        return None
# ── 데이터 저장 ─────────────────────────────

def save_to_db(temperature, humidity):
    conn   = get_connection()
    cursor = conn.cursor()
    sql    = "INSERT INTO sensor_data (temperature, humidity) VALUES (%s, %s)"
    cursor.execute(sql, (temperature, humidity))
    conn.commit()
    cursor.close()
    conn.close()
# ── 데이터 조회 ─────────────────────────────

def get_records(limit=10):
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM sensor_data ORDER BY recorded_at DESC LIMIT %s",
        (limit,)

    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
# ── 전체 개수 구하는 함수 ─────────────────────────────
def get_total_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sensor_data")
    (cnt,) = cursor.fetchone()
    cursor.close()
    conn.close()
    return cnt
# ── 라우트 ──────────────────────────────────
@app.route('/')
def index():
    records = get_records(limit=10)
    total_count = get_total_count()
    return render_template("index.html", records=records, total_count=total_count)

@app.route('/collect')
def collect():
    data = read_sensor()
    if data:
        save_to_db(data["temperature"], data["humidity"])
        return f"저장 완료: 온도 {data['temperature']}°C, 습도 {data['humidity']}%"
    else:
        return "센서 데이터를 읽을 수 없습니다.", 500
# esp32에서 보낸값을 db에 저장 Get과 Post
@app.route("/products/arduino", methods=["GET", "POST"])
def products_arduino():
    # GET: /products/arduino?temperature=26&humidity=70
    # 일단은 우리가 연습이고 하니까 Get으로 저장할 수 있는 로직으로 만든거
    if request.method == "GET":
        temp = request.args.get("temperature", type=float)
        humi = request.args.get("humidity", type=float)
    else:
        # POST: body "temperature=26&humidity=70" (x-www-form-urlencoded)
        # POST 요청이 오면 값으로 바꿔서 저장
        temp = request.form.get("temperature", type=float)
        humi = request.form.get("humidity", type=float)

    if temp is None or humi is None:
        return "temperature/humidity 값이 없습니다", 400

    save_to_db(temp, humi)
    return f"OK 저장됨 temp={temp}, humi={humi}\n", 200   

# 주기적으로 수집하고 저장하는 함수
def auto_collect(interval=10):
    """interval초마다 센서 데이터를 자동으로 수집·저장"""
    while True:
        data = read_sensor()
        if data:
            save_to_db(data["temperature"], data["humidity"])
            print(f"저장됨: {data['temperature']}°C, {data['humidity']}%")
        time.sleep(interval)

# 오토컬렉팅? 임시 주석
# 주기적으로 새로고침인가?
# 지금은 잠시 주석처리함
# 아닌거같은데
# thread = threading.Thread(target=auto_collect, args=(10,), daemon=True)
# thread.start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
