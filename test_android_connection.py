#!/usr/bin/env python3
"""
Простой тест TCP соединения с Android Agent
"""
import socket
import json
import time

def test_android_connection():
    print("Testing Android Agent TCP connection...")
    
    try:
        # Подключаемся к Android через ADB port forwarding
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('localhost', 4444))
        print("✅ Connected to Android Agent")
        
        # Отправляем команду TAP
        command = {
            "type": "TAP",
            "x": 0.5,
            "y": 0.5,
            "sequence": 1,
            "execTimeDeviceMs": int(time.time() * 1000) + 1000
        }
        
        message = json.dumps(command) + '\n'
        sock.send(message.encode())
        print(f"✅ Sent TAP command: {command}")
        
        # Получаем ответ
        response = sock.recv(1024).decode().strip()
        if response:
            response_data = json.loads(response)
            print(f"✅ Received response: {response_data}")
            
            if response_data.get('success'):
                print("🎉 TAP command executed successfully!")
            else:
                print(f"❌ TAP command failed: {response_data.get('message')}")
        else:
            print("❌ No response received")
            
        sock.close()
        
    except ConnectionRefusedError:
        print("❌ Connection refused - make sure:")
        print("   1. Android device is connected")
        print("   2. MirrorSync Agent is installed and running")
        print("   3. Accessibility Service is enabled")
        print("   4. Port forwarding is set up: adb forward tcp:4444 tcp:4444")
        
    except socket.timeout:
        print("❌ Connection timeout")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_android_connection()