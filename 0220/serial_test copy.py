import serial

import time

# 포트 이름은 본인 환경에 맞게 변경

# Windows: "COM3", "COM4" 등

# Mac/Linux: "/dev/ttyUSB0", "/dev/ttyACM0" 등

ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=3)

time.sleep(2)  # Arduino 리셋 대기

for _ in range(5):

    line = ser.readline()          # 한 줄 읽기 (bytes)

    print("원본:", line)

    decoded = line.decode("utf-8").strip()  # 문자열로 변환, 공백 제거

    print("변환:", decoded)

ser.close()
