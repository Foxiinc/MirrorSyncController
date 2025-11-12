#!/usr/bin/env python3
"""
Прямой тест команд на Android через ADB
"""

import subprocess
import time

def test_direct_tap():
    device = "953aeed3"
    adb_cmd = "C:\\platform-tools\\adb.exe"
    
    print("Testing direct ADB tap...")
    
    # Прямой тап через ADB input
    result = subprocess.run([
        adb_cmd, '-s', device, 'shell', 'input', 'tap', '500', '1000'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("[OK] Direct ADB tap successful")
    else:
        print(f"[FAIL] Direct ADB tap failed: {result.stderr}")
    
    time.sleep(1)
    
    # Тест свайпа
    result = subprocess.run([
        adb_cmd, '-s', device, 'shell', 'input', 'swipe', '300', '1000', '700', '1000', '500'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("[OK] Direct ADB swipe successful")
    else:
        print(f"[FAIL] Direct ADB swipe failed: {result.stderr}")

if __name__ == "__main__":
    test_direct_tap()