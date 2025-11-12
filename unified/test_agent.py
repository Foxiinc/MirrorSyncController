#!/usr/bin/env python3
"""
Тест подключения к Android агенту
"""

import socket
import json
import time

def test_agent_connection():
    print("Testing Android agent connection...")
    
    try:
        # Подключаемся к агенту через port forwarding
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        # Пробуем IPv4 и IPv6
        try:
            sock.connect(('127.0.0.1', 4444))
        except:
            sock.close()
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(('::1', 4444))
        
        # Отправляем PING
        ping_cmd = {"type": "PING"}
        message = json.dumps(ping_cmd) + "\n"
        sock.send(message.encode('utf-8'))
        
        # Читаем ответ
        response = sock.recv(1024).decode('utf-8')
        print(f"Agent response: {response}")
        
        # Тестируем TAP команду
        tap_cmd = {
            "type": "TAP",
            "x": 0.5,
            "y": 0.5,
            "seq": 1,
            "exec_time_device_ms": int(time.time() * 1000) + 100
        }
        message = json.dumps(tap_cmd) + "\n"
        sock.send(message.encode('utf-8'))
        
        response = sock.recv(1024).decode('utf-8')
        print(f"Tap response: {response}")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"Agent connection failed: {e}")
        return False

if __name__ == "__main__":
    test_agent_connection()