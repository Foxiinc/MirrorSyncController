#!/usr/bin/env python3
"""
Тест исправлений координат и системных кнопок
"""
import socket
import json
import time

def test_tap_coordinates():
    """Тест точности координат"""
    print("=== Testing TAP coordinates ===")
    
    test_coords = [
        (0.1, 0.1, "Top-left corner"),
        (0.5, 0.5, "Center"),
        (0.9, 0.9, "Bottom-right corner"),
        (0.0, 0.0, "Exact top-left"),
        (1.0, 1.0, "Exact bottom-right")
    ]
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect(('localhost', 4444))
        
        for x, y, desc in test_coords:
            command = {
                "type": "TAP",
                "x": x,
                "y": y,
                "sequence": int(time.time()),
                "execTimeDeviceMs": int(time.time() * 1000) + 500
            }
            
            message = json.dumps(command) + '\n'
            sock.send(message.encode())
            print(f"✅ Sent TAP {desc}: ({x}, {y})")
            
            # Небольшая пауза между командами
            time.sleep(1)
            
        sock.close()
        print("✅ Coordinate test completed")
        
    except Exception as e:
        print(f"❌ Coordinate test failed: {e}")

def test_system_keys():
    """Тест системных кнопок"""
    print("\n=== Testing System Keys ===")
    
    test_keys = [
        (3, "Home"),
        (4, "Back"), 
        (82, "Menu"),
        (187, "Recent Apps")
    ]
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect(('localhost', 4444))
        
        for key_code, desc in test_keys:
            command = {
                "type": "KEY",
                "keyCode": key_code,
                "sequence": int(time.time()),
                "execTimeDeviceMs": int(time.time() * 1000) + 500
            }
            
            message = json.dumps(command) + '\n'
            sock.send(message.encode())
            print(f"✅ Sent {desc} key (code: {key_code})")
            
            # Пауза между системными командами
            time.sleep(2)
            
        sock.close()
        print("✅ System keys test completed")
        
    except Exception as e:
        print(f"❌ System keys test failed: {e}")

def test_swipe_gestures():
    """Тест свайпов"""
    print("\n=== Testing SWIPE gestures ===")
    
    test_swipes = [
        (0.5, 0.8, 0.5, 0.2, 500, "Swipe up"),
        (0.5, 0.2, 0.5, 0.8, 500, "Swipe down"),
        (0.2, 0.5, 0.8, 0.5, 500, "Swipe right"),
        (0.8, 0.5, 0.2, 0.5, 500, "Swipe left")
    ]
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect(('localhost', 4444))
        
        for x1, y1, x2, y2, duration, desc in test_swipes:
            command = {
                "type": "SWIPE",
                "x": x1,
                "y": y1,
                "endX": x2,
                "endY": y2,
                "durationMs": duration,
                "sequence": int(time.time()),
                "execTimeDeviceMs": int(time.time() * 1000) + 500
            }
            
            message = json.dumps(command) + '\n'
            sock.send(message.encode())
            print(f"✅ Sent {desc}: ({x1},{y1}) → ({x2},{y2})")
            
            time.sleep(1.5)
            
        sock.close()
        print("✅ Swipe test completed")
        
    except Exception as e:
        print(f"❌ Swipe test failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing MirrorSync fixes...")
    print("Make sure:")
    print("1. Android device is connected")
    print("2. MirrorSync Agent is running")
    print("3. Accessibility Service is enabled")
    print("4. Port forwarding: adb forward tcp:4444 tcp:4444")
    print()
    
    input("Press Enter to start tests...")
    
    test_tap_coordinates()
    test_system_keys()
    test_swipe_gestures()
    
    print("\n🎉 All tests completed!")
    print("Check your Android device to see if actions were performed correctly.")