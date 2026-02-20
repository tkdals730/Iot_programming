from flask import Flask,render_template, jsonify
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
        ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=2)
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

# ── 라우트 ──────────────────────────────────
@app.route('/')
def index():
    records = get_records()
    return render_template("index.html", records=records)

@app.route('/collect')
def collect():
    data = read_sensor()
    if data:
        save_to_db(data["temperature"], data["humidity"])
        return f"저장 완료: 온도 {data['temperature']}°C, 습도 {data['humidity']}%"
    else:
        return "센서 데이터를 읽을 수 없습니다.", 500
def auto_collect(interval=10):
    """interval초마다 센서 데이터를 자동으로 수집·저장"""
    while True:
        data = read_sensor()
        if data:
            save_to_db(data["temperature"], data["humidity"])
            print(f"저장됨: {data['temperature']}°C, {data['humidity']}%")
        time.sleep(interval)

# if __name__ == '__main__': 바로 위에 추가

thread = threading.Thread(target=auto_collect, args=(10,), daemon=True)

thread.start()

if __name__ == '__main__':
    app.run(debug=True)
