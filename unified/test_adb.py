#!/usr/bin/env python3
"""
Тест ADB подключения и команд
"""

import subprocess
import sys

def test_adb():
    print("Testing ADB connection...")
    
    # Проверяем ADB
    try:
        result = subprocess.run(['adb', 'version'], capture_output=True, text=True)
        print(f"ADB version: {result.stdout.strip()}")
    except FileNotFoundError:
        print("ADB not found in PATH")
        return False
    
    # Список устройств
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        print(f"Connected devices:\n{result.stdout}")
        
        lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
        devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
        
        if not devices:
            print("No devices connected")
            return False
            
        device = devices[0]
        print(f"Using device: {device}")
        
        # Тест скриншота
        print("Testing screenshot...")
        result = subprocess.run(['adb', '-s', device, 'shell', 'screencap', '-p'], 
                              capture_output=True)
        if result.returncode == 0:
            print(f"Screenshot OK, size: {len(result.stdout)} bytes")
        else:
            print("Screenshot failed")
            
        # Тест port forwarding
        print("Testing port forwarding...")
        result = subprocess.run(['adb', '-s', device, 'forward', 'tcp:4444', 'tcp:4444'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Port forwarding OK")
        else:
            print(f"Port forwarding failed: {result.stderr}")
            
        # Проверяем агент
        print("Checking if MirrorSync agent is running...")
        result = subprocess.run(['adb', '-s', device, 'shell', 'ps | grep mirrorsync'], 
                              capture_output=True, text=True)
        if 'mirrorsync' in result.stdout.lower():
            print("MirrorSync agent is running")
        else:
            print("MirrorSync agent NOT running - install APK and enable Accessibility Service")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_adb()