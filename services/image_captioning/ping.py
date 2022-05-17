import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while True:
    try:
        s.connect(("0.0.0.0", 8125))
        break
    except:
        time.sleep(60)