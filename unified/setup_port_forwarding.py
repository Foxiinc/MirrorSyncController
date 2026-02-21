#!/usr/bin/env python3
"""
Автоматическая настройка port forwarding для устройств
"""
import subprocess
import sys
import os

def setup_port_forwarding():
    """Настраивает port forwarding для всех подключенных устройств"""
    try:
        # Получаем список устройств
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        if result.returncode != 0:
            print("ADB не найден или не работает")
            return False
            
        devices = []
        for line in result.stdout.split('\n'):
            if '\tdevice' in line:
                serial = line.split('\t')[0]
                devices.append(serial)
        
        if not devices:
            print("Устройства не найдены")
            return False
            
        print(f"Найдено устройств: {len(devices)}")
        
        # Настраиваем forwarding для каждого устройства
        for i, serial in enumerate(devices):
            port = 8080 + int(serial[-4:], 16) % 1000
            
            # Настраиваем port forwarding (Android слушает на 8080)
            cmd = ['adb', '-s', serial, 'forward', f'tcp:{port}', 'tcp:8080']
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0:
                print(f"✓ {serial}: localhost:{port} -> device:8080")
            else:
                print(f"✗ {serial}: Ошибка настройки forwarding")
                
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

if __name__ == "__main__":
    if setup_port_forwarding():
        print("\nPort forwarding настроен. Запускайте приложение.")
    else:
        print("\nОшибка настройки port forwarding")
        sys.exit(1)