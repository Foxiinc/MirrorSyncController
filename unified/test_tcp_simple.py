#!/usr/bin/env python3
import socket
import json
import time

def test_tcp():
    print("Testing TCP connection to Android agent...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        
        print("Connecting to 127.0.0.1:4444...")
        sock.connect(('127.0.0.1', 4444))
        print("Connected!")
        
        # Простой PING
        ping = {"type": "PING"}
        msg = json.dumps(ping) + "\n"
        print(f"Sending: {msg.strip()}")
        
        sock.send(msg.encode())
        
        # Читаем ответ
        data = sock.recv(1024)
        print(f"Received: {data.decode().strip()}")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"TCP test failed: {e}")
        return False

if __name__ == "__main__":
    test_tcp()