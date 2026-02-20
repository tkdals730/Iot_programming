import serial
import time

#시리얼 포트 설정
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)  # 리셋

try:
        while True:
                if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8').rstrip()
                        humidity, celsius = line.split(',')
                        humidity = float(humidity)
                        celsius = float(celsius)
                        print(f"습도: {humidity}%, 온도: {celsius} C")

except KeyboardInterrupt:
        print("\n프로그램 종료")
        ser.close()